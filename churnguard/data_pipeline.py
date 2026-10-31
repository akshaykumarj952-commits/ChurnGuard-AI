"""Phase 1 - load and clean the UCI Online Retail transactions.

Design rules
------------
* Nothing is dropped silently. Every exclusion is recorded in an audit log
  with the rule, the number of rows removed and the value (Quantity x
  UnitPrice) removed.
* Cancellations are kept in a SEPARATE table (they are not purchases, but
  they carry information such as a customer's return behaviour).
* Rows without a CustomerID cannot be linked to a customer. They are
  excluded from customer analysis but their size is reported.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import PipelineConfig

REQUIRED_COLUMNS = [
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country",
]


@dataclass
class CleanResult:
    valid: pd.DataFrame           # genuine purchases by identified customers
    cancellations: pd.DataFrame   # cancellation lines by identified customers
    audit: list                   # ordered list of exclusion steps
    summary: dict                 # headline numbers for reporting
    data_start: pd.Timestamp
    data_end: pd.Timestamp        # latest timestamp in the RAW file


def load_raw(path) -> pd.DataFrame:
    """Read the UCI Excel file and check that the expected columns exist."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. See README for download instructions."
        )
    raw = pd.read_excel(
        path, engine="openpyxl", dtype={"InvoiceNo": str, "StockCode": str}
    )
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Dataset is missing expected columns: {missing}")
    return raw


def _step(audit: list, df: pd.DataFrame, mask: pd.Series, name: str, rule: str, note: str = ""):
    """Remove rows where mask is True; record the step. Returns (kept, removed)."""
    removed = df.loc[mask]
    kept = df.loc[~mask]
    audit.append({
        "step": name,
        "rule": rule,
        "rows_before": int(len(df)),
        "rows_removed": int(len(removed)),
        "rows_after": int(len(kept)),
        "line_value_removed": round(float(removed["line_value"].sum()), 2),
        "note": note,
    })
    return kept, removed


def clean_transactions(raw: pd.DataFrame, config: PipelineConfig | None = None) -> CleanResult:
    config = config or PipelineConfig()
    audit: list = []

    df = raw.loc[:, REQUIRED_COLUMNS].copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["line_value"] = df["Quantity"] * df["UnitPrice"]

    raw_rows = int(len(df))
    data_start = df["InvoiceDate"].min()
    data_end = df["InvoiceDate"].max()
    raw_customers = int(df["CustomerID"].nunique())

    # Informational counts (not exclusions).
    non_c_alpha_invoices = int(
        (df["InvoiceNo"].str.match(r"^[A-Za-z]") & ~df["InvoiceNo"].str.upper().str.startswith("C")).sum()
    )

    # 0. Unparseable timestamps / numbers.
    bad = df["InvoiceDate"].isna() | df["Quantity"].isna() | df["UnitPrice"].isna()
    df, _ = _step(audit, df, bad, "0_unparseable",
                  "InvoiceDate, Quantity or UnitPrice could not be read")

    # 1. Missing CustomerID.
    no_id = df["CustomerID"].isna()
    anonymous_rows = int(no_id.sum())
    anonymous_positive_value = float(df.loc[no_id & (df["line_value"] > 0), "line_value"].sum())
    df, _ = _step(audit, df, no_id, "1_missing_customer_id",
                  "CustomerID is blank; transaction cannot be linked to a customer",
                  "Excluded from customer-level analysis only. Their size is reported "
                  "in summary['anonymous_*'] so the exclusion is visible.")
    df["CustomerID"] = df["CustomerID"].astype("int64").astype(str)

    # 2. Cancellations (separate table, not purchases).
    is_cancel = df["InvoiceNo"].str.upper().str.startswith("C")
    df, cancel = _step(audit, df, is_cancel, "2_cancellations",
                       "InvoiceNo starts with 'C' (UCI: cancellation)",
                       "Moved to a separate table; never counted as a purchase.")

    # 3. Non-positive quantity or price among the remaining rows.
    n_qty = int((df["Quantity"] <= 0).sum())
    n_price = int((df["UnitPrice"] <= 0).sum())
    invalid = (df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)
    df, _ = _step(audit, df, invalid, "3_non_positive_qty_or_price",
                  "Quantity <= 0 or UnitPrice <= 0 on a non-cancellation row",
                  f"{n_qty} rows with Quantity<=0, {n_price} rows with UnitPrice<=0 "
                  "(a row can be in both).")

    # 4. Non-product stock codes (postage, fees, manual entries ...).
    codes = set(c.upper() for c in config.non_product_codes)
    nonprod = df["StockCode"].isin(codes)
    df, _ = _step(audit, df, nonprod, "4_non_product_codes",
                  "StockCode is a service/fee code, not a product: " + ", ".join(sorted(codes)),
                  "Postage, carriage, manual entries, fees etc. are not product purchases.")
    # Same codes are also removed from the cancellation table (e.g. Discount, CRUK).
    cancel_before = int(len(cancel))
    cancel = cancel.loc[~cancel["StockCode"].isin(codes)]
    cancel_nonprod_dropped = cancel_before - int(len(cancel))

    # 5. Exact duplicate rows: reported; dropped only if configured.
    dup_mask = df.duplicated(keep="first")
    n_dups = int(dup_mask.sum())
    if config.drop_duplicate_rows:
        df, _ = _step(audit, df, dup_mask, "5_exact_duplicates",
                      "Row identical to an earlier row in every column")
    else:
        audit.append({
            "step": "5_exact_duplicates", "rule": "Reported only (not removed)",
            "rows_before": int(len(df)), "rows_removed": 0, "rows_after": int(len(df)),
            "line_value_removed": 0.0,
            "note": f"{n_dups} rows are exact duplicates of an earlier row. They may be genuine "
                    "repeated scan lines, so they are kept by default "
                    "(set drop_duplicate_rows=True to test sensitivity).",
        })

    valid = df.reset_index(drop=True)
    cancel = cancel.reset_index(drop=True)

    summary = {
        "raw_rows": raw_rows,
        "raw_customers_with_id": raw_customers,
        "data_start": str(data_start),
        "data_end": str(data_end),
        "anonymous_rows": anonymous_rows,
        "anonymous_rows_share_pct": round(100 * anonymous_rows / raw_rows, 2),
        "anonymous_positive_line_value": round(anonymous_positive_value, 2),
        "non_c_alpha_invoices": non_c_alpha_invoices,
        "cancellation_rows_kept": int(len(cancel)),
        "cancellation_nonproduct_rows_dropped": cancel_nonprod_dropped,
        "valid_rows": int(len(valid)),
        "valid_customers": int(valid["CustomerID"].nunique()),
        "valid_invoices": int(valid["InvoiceNo"].nunique()),
        "valid_revenue": round(float(valid["line_value"].sum()), 2),
        "exact_duplicate_rows_in_valid": n_dups,
        "currency": "GBP (UCI lists UnitPrice in sterling)",
    }
    return CleanResult(valid, cancel, audit, summary, data_start, data_end)
