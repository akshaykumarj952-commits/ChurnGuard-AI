"""Phase 2 - customer features (RFM) at a cutoff, plus the future outcome.

Temporal design (this is what prevents leakage)
-----------------------------------------------
        history (features)            |      observation window (outcome)
  ... ------------------------- cutoff | cutoff+1 ---------- cutoff+window_days

* Features use ONLY valid purchases / cancellations dated on or before the
  cutoff day (inclusive, i.e. up to 23:59:59 of the cutoff date).
* The outcome uses ONLY valid purchases in the window that follows.
* Only customers with >= 1 valid purchase in the history are eligible.
* The window must be fully observed. The final calendar day of the raw file
  is treated as incomplete (the UCI file stops at 12:50 on its last day), so
  the window may not extend into it.

The outcome is an operational INACTIVITY PROXY: "no valid purchase in the
next N days". It does not prove that a customer permanently left.
"""
from __future__ import annotations

import pandas as pd

from .config import PipelineConfig

# Column groups. Tests use these to prove no outcome column is a feature.
ID_COLUMN = "customer_id"
FEATURE_COLUMNS = [
    "recency_days", "frequency", "monetary", "avg_order_value", "total_units",
    "tenure_days", "first_purchase_date", "last_purchase_date",
    "n_cancel_invoices", "cancel_value", "cancel_value_ratio",
    "country", "is_uk",
]
OUTCOME_COLUMNS = ["outcome_orders_in_window", "outcome_revenue_in_window", "outcome_inactive"]


def check_window(config: PipelineConfig, data_start: pd.Timestamp, data_end: pd.Timestamp):
    """Validate the cutoff/window against the actual data. Returns key dates."""
    cutoff = pd.Timestamp(config.cutoff_date).normalize()
    window_start = cutoff + pd.Timedelta(days=1)
    window_end = cutoff + pd.Timedelta(days=int(config.window_days))  # inclusive day
    last_complete_day = data_end.normalize() - pd.Timedelta(days=1)

    if cutoff < data_start.normalize():
        raise ValueError(f"Cutoff {cutoff.date()} is before the data starts ({data_start.date()}).")
    if window_end > last_complete_day:
        latest_ok = last_complete_day - pd.Timedelta(days=int(config.window_days))
        raise ValueError(
            f"Observation window ends {window_end.date()}, but the last COMPLETE day of data is "
            f"{last_complete_day.date()} (the file ends {data_end}). The window would not be fully "
            f"observed. Use a cutoff on or before {latest_ok.date()} or a shorter window."
        )
    return cutoff, window_start, window_end, last_complete_day


def build_customer_table(valid: pd.DataFrame, cancellations: pd.DataFrame,
                         config: PipelineConfig, data_start: pd.Timestamp,
                         data_end: pd.Timestamp):
    """Return (customer_table, metadata). One row per eligible customer."""
    cutoff, window_start, window_end, last_complete_day = check_window(config, data_start, data_end)
    hist_limit = cutoff + pd.Timedelta(days=1)        # exclusive upper bound
    window_limit = window_end + pd.Timedelta(days=1)  # exclusive upper bound

    hist = valid.loc[valid["InvoiceDate"] < hist_limit]
    window = valid.loc[(valid["InvoiceDate"] >= hist_limit) & (valid["InvoiceDate"] < window_limit)]
    cancel_hist = cancellations.loc[cancellations["InvoiceDate"] < hist_limit]

    if hist.empty:
        raise ValueError("No valid purchases on or before the cutoff.")
    # Leakage guard #1: nothing after the cutoff may be in the history.
    assert hist["InvoiceDate"].max() < hist_limit

    g = hist.groupby("CustomerID")
    feats = g.agg(
        first_purchase_ts=("InvoiceDate", "min"),
        last_purchase_ts=("InvoiceDate", "max"),
        frequency=("InvoiceNo", "nunique"),
        monetary=("line_value", "sum"),
        total_units=("Quantity", "sum"),
    )
    feats["first_purchase_date"] = feats["first_purchase_ts"].dt.normalize()
    feats["last_purchase_date"] = feats["last_purchase_ts"].dt.normalize()
    feats["recency_days"] = (cutoff - feats["last_purchase_date"]).dt.days
    feats["tenure_days"] = (cutoff - feats["first_purchase_date"]).dt.days
    feats["avg_order_value"] = feats["monetary"] / feats["frequency"]
    feats["monetary"] = feats["monetary"].round(2)
    feats["avg_order_value"] = feats["avg_order_value"].round(2)

    # Country of the most recent invoice (8 customers appear under >1 country).
    feats["country"] = hist.sort_values("InvoiceDate", kind="stable").groupby("CustomerID")["Country"].last()
    feats["is_uk"] = (feats["country"] == "United Kingdom").astype(int)

    # Cancellation behaviour BEFORE the cutoff (a separate signal, not a purchase).
    cg = cancel_hist.groupby("CustomerID")
    feats["n_cancel_invoices"] = cg["InvoiceNo"].nunique().reindex(feats.index).fillna(0).astype(int)
    feats["cancel_value"] = (-cg["line_value"].sum()).reindex(feats.index).fillna(0.0).round(2)
    feats["cancel_value_ratio"] = (feats["cancel_value"] / feats["monetary"]).round(4)

    # Outcome from the window only.
    wg = window.groupby("CustomerID")
    feats["outcome_orders_in_window"] = wg["InvoiceNo"].nunique().reindex(feats.index).fillna(0).astype(int)
    feats["outcome_revenue_in_window"] = wg["line_value"].sum().reindex(feats.index).fillna(0.0).round(2)
    feats["outcome_inactive"] = (feats["outcome_orders_in_window"] == 0).astype(int)

    table = feats.reset_index().rename(columns={"CustomerID": ID_COLUMN})
    table = table[[ID_COLUMN] + FEATURE_COLUMNS + OUTCOME_COLUMNS].sort_values(ID_COLUMN).reset_index(drop=True)

    first_ever = valid.groupby("CustomerID")["InvoiceDate"].min()
    n_new_after_cutoff = int((first_ever >= hist_limit).sum())
    metadata = {
        "cutoff_date": str(cutoff.date()),
        "window_start": str(window_start.date()),
        "window_end": str(window_end.date()),
        "window_days": int(config.window_days),
        "last_complete_day_in_data": str(last_complete_day.date()),
        "eligible_customers": int(len(table)),
        "inactive_customers": int(table["outcome_inactive"].sum()),
        "active_customers": int((table["outcome_inactive"] == 0).sum()),
        "inactivity_rate": round(float(table["outcome_inactive"].mean()), 4),
        "valid_customers_total": int(valid["CustomerID"].nunique()),
        "customers_first_seen_after_cutoff_excluded": n_new_after_cutoff,
        "history_rows": int(len(hist)),
        "window_rows": int(len(window)),
        "recency_definition": "days from the customer's last valid purchase date to the cutoff date (0 = purchased on cutoff day)",
        "frequency_definition": "number of distinct valid invoices on or before the cutoff",
        "monetary_definition": "sum of Quantity x UnitPrice over valid product lines on or before the cutoff (GBP)",
        "outcome_definition": "outcome_inactive = 1 if the customer has no valid purchase in the observation window",
    }
    return table, metadata
