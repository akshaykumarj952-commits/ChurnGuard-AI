"""Validation tests for the ChurnGuard data pipeline (Phases 1-3).

Run from the project folder (no extra packages needed):

    python -m unittest tests.test_pipeline -v

Part A uses a tiny hand-made dataset whose correct answers were worked out
by hand, so it runs in a second and needs no download.
Part B runs the full pipeline on the real UCI file. It is skipped if the file
is not found. Point to it with the CHURNGUARD_RAW environment variable or put
it at data/raw/Online Retail.xlsx.
"""
import os
import unittest
from pathlib import Path

import pandas as pd

from churnguard.config import PipelineConfig
from churnguard.data_pipeline import clean_transactions, load_raw
from churnguard.features import (FEATURE_COLUMNS, OUTCOME_COLUMNS, build_customer_table,
                                 check_window)


def _row(inv, code, qty, ts, price, cust, country="United Kingdom", desc="ITEM"):
    return dict(InvoiceNo=inv, StockCode=code, Description=desc, Quantity=qty,
                InvoiceDate=pd.Timestamp(ts), UnitPrice=price, CustomerID=cust, Country=country)


def synthetic_raw():
    """Hand-made data. Cutoff 2011-03-31, window 30 days -> window 04-01..04-30.
    The file ends 2011-05-05 12:00, so the last complete day is 2011-05-04."""
    rows = [
        # 1001: two valid invoices before cutoff, one in window (active)
        _row("1", "A1", 2, "2011-03-01 10:00", 5.0, 1001),
        _row("1", "A2", 1, "2011-03-01 10:00", 3.0, 1001),
        _row("2", "A1", 4, "2011-03-20 09:00", 2.5, 1001),
        _row("3", "POST", 1, "2011-03-22 09:00", 10.0, 1001),          # postage only invoice -> excluded
        _row("C3", "A2", -1, "2011-03-25 09:00", 3.0, 1001),           # cancellation
        _row("4", "A1", 1, "2011-04-10 09:00", 5.0, 1001),             # in window
        _row("5", "A1", 1, "2011-05-05 12:00", 5.0, 1001),             # after window; sets data end
        # 1002: one old purchase, nothing in window (inactive)
        _row("6", "A1", 1, "2011-02-01 09:00", 4.0, 1002),
        _row("7", "A1", 1, "2011-03-10 09:00", 0.0, 1002),             # zero price -> excluded
        # 1003: first purchase AFTER cutoff -> not eligible
        _row("8", "A1", 1, "2011-04-15 09:00", 4.0, 1003),
        # 1004: purchase at 23:59 on the cutoff day -> in history, recency 0
        _row("9", "A1", 1, "2011-03-31 23:59", 4.0, 1004),
        # 1005: history purchase + purchase at 23:30 on the LAST window day -> active
        _row("10", "A1", 1, "2011-03-02 09:00", 4.0, 1005),
        _row("11", "A1", 1, "2011-04-30 23:30", 4.0, 1005),
        # 1006: history purchase, next purchase is AFTER the window -> inactive
        _row("12", "A1", 1, "2011-03-05 09:00", 4.0, 1006),
        _row("13", "A1", 1, "2011-05-03 09:00", 4.0, 1006),
        # 1007: history purchase + purchase at 00:00:00 on the FIRST window day.
        # An off-by-one that lets that day into the history would flip this customer.
        _row("16", "A1", 2, "2011-03-10 09:00", 4.0, 1007),
        _row("17", "A1", 1, "2011-04-01 00:00", 4.0, 1007),
        # 1008: history purchase; next purchase at 00:00:00 on the day AFTER the window ends.
        # An off-by-one that lengthens the window would wrongly make this customer active.
        _row("18", "A1", 1, "2011-03-12 09:00", 4.0, 1008),
        _row("19", "A1", 1, "2011-05-01 00:00", 4.0, 1008),
        # no CustomerID, and an 'A' invoice with negative price
        _row("14", "A1", 3, "2011-03-05 09:00", 4.0, None),
        _row("A15", "B", 1, "2011-03-06 09:00", -50.0, 1002),
    ]
    return pd.DataFrame(rows)


SYN_CFG = PipelineConfig(cutoff_date="2011-03-31", window_days=30)


class TestSynthetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = synthetic_raw()
        cls.res = clean_transactions(cls.raw, SYN_CFG)
        cls.table, cls.meta = build_customer_table(
            cls.res.valid, cls.res.cancellations, SYN_CFG, cls.res.data_start, cls.res.data_end)
        cls.t = cls.table.set_index("customer_id")

    def test_row_accounting_reconciles(self):
        # Each step's "after" equals the next step's "before"; final == valid rows.
        steps = [a for a in self.res.audit if a["step"] != "5_exact_duplicates"]
        for a in steps:
            self.assertEqual(a["rows_before"] - a["rows_removed"], a["rows_after"])
        for a, b in zip(self.res.audit, self.res.audit[1:]):
            self.assertEqual(a["rows_after"], b["rows_before"])
        self.assertEqual(self.res.audit[-1]["rows_after"], len(self.res.valid))
        self.assertEqual(self.res.audit[0]["rows_before"], len(self.raw))

    def test_exclusions(self):
        self.assertEqual(self.res.summary["anonymous_rows"], 1)
        self.assertEqual(len(self.res.cancellations), 1)
        self.assertFalse(self.res.valid["InvoiceNo"].str.startswith("C").any())
        self.assertTrue((self.res.valid["Quantity"] > 0).all())
        self.assertTrue((self.res.valid["UnitPrice"] > 0).all())
        self.assertNotIn("POST", set(self.res.valid["StockCode"]))
        self.assertEqual(self.res.summary["non_c_alpha_invoices"], 1)

    def test_eligible_customers(self):
        self.assertEqual(set(self.t.index), {"1001", "1002", "1004", "1005", "1006", "1007", "1008"})
        self.assertNotIn("1003", self.t.index)  # first purchase after cutoff

    def test_hand_computed_features(self):
        r = self.t.loc["1001"]
        self.assertEqual(r["frequency"], 2)                 # POST-only invoice not counted
        self.assertAlmostEqual(r["monetary"], 23.0)         # 2*5 + 1*3 + 4*2.5
        self.assertEqual(r["recency_days"], 11)             # 03-31 minus 03-20
        self.assertEqual(r["n_cancel_invoices"], 1)
        self.assertAlmostEqual(r["cancel_value"], 3.0)
        self.assertEqual(self.t.loc["1002", "recency_days"], 58)  # 03-31 minus 02-01
        self.assertEqual(self.t.loc["1004", "recency_days"], 0)   # bought on cutoff day
        # 1007's 04-01 00:00 purchase is the FUTURE: it must not touch the features.
        self.assertEqual(self.t.loc["1007", "recency_days"], 21)  # 03-31 minus 03-10
        self.assertEqual(self.t.loc["1007", "frequency"], 1)
        self.assertAlmostEqual(self.t.loc["1007", "monetary"], 8.0)

    def test_outcome_boundaries(self):
        inactive = self.t["outcome_inactive"].to_dict()
        self.assertEqual(inactive["1001"], 0)  # purchase 04-10
        self.assertEqual(inactive["1005"], 0)  # purchase at 23:30 on last window day: counts
        self.assertEqual(inactive["1002"], 1)
        self.assertEqual(inactive["1004"], 1)
        self.assertEqual(inactive["1006"], 1)  # next purchase is after the window
        self.assertEqual(inactive["1007"], 0)  # 04-01 00:00:00 is the first second of the window
        self.assertEqual(inactive["1008"], 1)  # 05-01 00:00:00 is the first second AFTER the window
        self.assertEqual(self.meta["inactive_customers"], 4)
        self.assertEqual(self.meta["eligible_customers"], 7)

    def test_no_outcome_column_is_a_feature(self):
        self.assertTrue(set(FEATURE_COLUMNS).isdisjoint(OUTCOME_COLUMNS))

    def test_leakage_future_data_cannot_change_features(self):
        # Delete EVERYTHING after the cutoff, rebuild features: must be identical.
        cutoff_end = pd.Timestamp("2011-04-01")
        v = self.res.valid.loc[self.res.valid["InvoiceDate"] < cutoff_end]
        c = self.res.cancellations.loc[self.res.cancellations["InvoiceDate"] < cutoff_end]
        # data_end must stay the same so the window check is unchanged
        t2, _ = build_customer_table(v, c, SYN_CFG, self.res.data_start, self.res.data_end)
        cols = ["customer_id"] + FEATURE_COLUMNS
        pd.testing.assert_frame_equal(
            self.table[cols].reset_index(drop=True), t2[cols].reset_index(drop=True))

    def test_leakage_future_values_cannot_change_features(self):
        # Wildly change post-cutoff quantities/prices: features must not move.
        v = self.res.valid.copy()
        after = v["InvoiceDate"] >= pd.Timestamp("2011-04-01")
        v.loc[after, ["Quantity", "UnitPrice"]] = [999, 999.0]
        v["line_value"] = v["Quantity"] * v["UnitPrice"]
        t2, _ = build_customer_table(v, self.res.cancellations, SYN_CFG,
                                     self.res.data_start, self.res.data_end)
        cols = ["customer_id"] + FEATURE_COLUMNS
        pd.testing.assert_frame_equal(
            self.table[cols].reset_index(drop=True), t2[cols].reset_index(drop=True))

    def test_incomplete_window_is_rejected(self):
        # Window ending on/after the last complete day (2011-05-04) must raise.
        bad = PipelineConfig(cutoff_date="2011-04-10", window_days=30)  # ends 05-10
        with self.assertRaises(ValueError):
            check_window(bad, self.res.data_start, self.res.data_end)
        edge = PipelineConfig(cutoff_date="2011-04-04", window_days=30)  # ends 05-04: allowed
        check_window(edge, self.res.data_start, self.res.data_end)
        edge2 = PipelineConfig(cutoff_date="2011-04-05", window_days=30)  # ends 05-05: partial day
        with self.assertRaises(ValueError):
            check_window(edge2, self.res.data_start, self.res.data_end)

    def test_duplicate_option(self):
        raw = pd.concat([self.raw, self.raw.iloc[[0]]], ignore_index=True)
        kept = clean_transactions(raw, SYN_CFG)
        self.assertEqual(kept.summary["exact_duplicate_rows_in_valid"], 1)
        dropped = clean_transactions(raw, PipelineConfig(cutoff_date="2011-03-31", window_days=30,
                                                         drop_duplicate_rows=True))
        self.assertEqual(len(dropped.valid), len(kept.valid) - 1)


# ----------------------------------------------------------------------------
# Part B: real data. Expected values are REGRESSION values taken from a verified
# run on the UCI file (541,909 rows); they should never change for the default
# configuration. If they do, something in the pipeline changed.
# ----------------------------------------------------------------------------
RAW_PATH = Path(os.environ.get("CHURNGUARD_RAW", Path("data") / "raw" / "Online Retail.xlsx"))


@unittest.skipUnless(RAW_PATH.exists(), f"Real dataset not found at {RAW_PATH}")
class TestRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = PipelineConfig()
        cls.raw = load_raw(RAW_PATH)
        cls.res = clean_transactions(cls.raw, cls.cfg)
        cls.table, cls.meta = build_customer_table(
            cls.res.valid, cls.res.cancellations, cls.cfg, cls.res.data_start, cls.res.data_end)

    def test_raw_shape(self):
        self.assertEqual(len(self.raw), 541909)

    def test_waterfall_numbers(self):
        steps = {a["step"]: a for a in self.res.audit}
        self.assertEqual(steps["1_missing_customer_id"]["rows_removed"], 135080)
        self.assertEqual(steps["2_cancellations"]["rows_removed"], 8905)
        self.assertEqual(steps["3_non_positive_qty_or_price"]["rows_removed"], 40)
        self.assertEqual(steps["4_non_product_codes"]["rows_removed"], 1544)
        self.assertEqual(len(self.res.valid), 396340)
        self.assertEqual(self.res.summary["valid_customers"], 4334)

    def test_row_accounting_reconciles(self):
        a = self.res.audit
        self.assertEqual(a[0]["rows_before"], 541909)
        for x, y in zip(a, a[1:]):
            self.assertEqual(x["rows_after"], y["rows_before"])
        removed = sum(s["rows_removed"] for s in a)
        self.assertEqual(541909 - removed, len(self.res.valid))

    def test_framework_numbers(self):
        self.assertEqual(self.meta["window_end"], "2011-12-08")
        self.assertEqual(self.meta["eligible_customers"], 3368)
        self.assertEqual(self.meta["inactive_customers"], 1451)
        self.assertEqual(self.meta["active_customers"], 1917)

    def test_table_sanity(self):
        t = self.table
        self.assertTrue(t["customer_id"].is_unique)
        self.assertTrue((t["frequency"] >= 1).all())
        self.assertTrue((t["monetary"] > 0).all())
        self.assertTrue((t["recency_days"] >= 0).all())
        self.assertTrue((t["last_purchase_date"] <= pd.Timestamp(self.cfg.cutoff_date)).all())
        self.assertTrue(t["outcome_inactive"].isin([0, 1]).all())
        self.assertEqual(int(t["outcome_inactive"].sum()), 1451)

    def test_label_matches_independent_recomputation(self):
        """Recompute the outcome straight from the raw file with different code."""
        r = self.raw
        inv = r["InvoiceNo"].astype(str)
        ok = (r["CustomerID"].notna() & ~inv.str.upper().str.startswith("C")
              & (r["Quantity"] > 0) & (r["UnitPrice"] > 0)
              & ~r["StockCode"].astype(str).str.upper().isin(self.cfg.non_product_codes))
        r = r.loc[ok]
        cutoff, end = pd.Timestamp("2011-09-09 23:59:59.999"), pd.Timestamp("2011-12-08 23:59:59.999")
        history_ids = set(r.loc[r["InvoiceDate"] <= cutoff, "CustomerID"].astype(int).astype(str))
        active_ids = set(r.loc[(r["InvoiceDate"] > cutoff) & (r["InvoiceDate"] <= end),
                              "CustomerID"].astype(int).astype(str))
        expected_inactive = history_ids - active_ids
        got_inactive = set(self.table.loc[self.table["outcome_inactive"] == 1, "customer_id"])
        self.assertEqual(set(self.table["customer_id"]), history_ids)
        self.assertEqual(got_inactive, expected_inactive)

    def test_leakage_on_real_data(self):
        cutoff_end = pd.Timestamp(self.cfg.cutoff_date) + pd.Timedelta(days=1)
        v = self.res.valid.loc[self.res.valid["InvoiceDate"] < cutoff_end]
        c = self.res.cancellations.loc[self.res.cancellations["InvoiceDate"] < cutoff_end]
        t2, _ = build_customer_table(v, c, self.cfg, self.res.data_start, self.res.data_end)
        cols = ["customer_id"] + FEATURE_COLUMNS
        pd.testing.assert_frame_equal(
            self.table[cols].reset_index(drop=True), t2[cols].reset_index(drop=True))

    def test_partial_final_day_rejected(self):
        with self.assertRaises(ValueError):  # the original 2011-09-10 idea ends on the partial day
            check_window(PipelineConfig(cutoff_date="2011-09-10"), self.res.data_start, self.res.data_end)


if __name__ == "__main__":
    unittest.main()
