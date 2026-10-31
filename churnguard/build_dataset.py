"""Build the processed customer-level dataset and the audit report.

Run from the project folder:

    python -m churnguard.build_dataset --input "data\\raw\\Online Retail.xlsx"

Options let you change the cutoff and window to test sensitivity:

    python -m churnguard.build_dataset --cutoff 2011-06-01 --window-days 90
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import PipelineConfig
from .data_pipeline import clean_transactions, load_raw
from .features import build_customer_table


def _fmt(n):
    return f"{n:,.2f}" if isinstance(n, float) else f"{n:,}"


def write_markdown_report(path: Path, config: PipelineConfig, result, meta: dict):
    s = result.summary
    lines = [
        "# ChurnGuard data audit",
        "",
        "Generated automatically by `churnguard.build_dataset`. Do not edit by hand.",
        "",
        "Source: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. "
        "https://doi.org/10.24432/C5BW33 (CC BY 4.0).",
        "",
        "## 1. Settings used",
        "",
        f"- Cutoff date (inclusive): **{meta['cutoff_date']}**",
        f"- Observation window: **{meta['window_start']} to {meta['window_end']}** ({meta['window_days']} days)",
        f"- Last complete day in the data: {meta['last_complete_day_in_data']} "
        f"(file ends {s['data_end']}; the final day is treated as incomplete)",
        f"- Duplicate rows dropped: {config.drop_duplicate_rows}",
        "",
        "## 2. Row-by-row exclusions (nothing is dropped silently)",
        "",
        "| Step | Rule | Rows before | Removed | Rows after | Line value removed |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for a in result.audit:
        lines.append(
            f"| {a['step']} | {a['rule']} | {_fmt(a['rows_before'])} | {_fmt(a['rows_removed'])} "
            f"| {_fmt(a['rows_after'])} | {_fmt(a['line_value_removed'])} |"
        )
    lines += ["", "Notes:", ""]
    for a in result.audit:
        if a["note"]:
            lines.append(f"- **{a['step']}**: {a['note']}")
    lines += [
        "",
        "## 3. What remains after cleaning",
        "",
        f"- Raw rows: {_fmt(s['raw_rows'])}",
        f"- Valid purchase rows: **{_fmt(s['valid_rows'])}**",
        f"- Customers with valid purchases: **{_fmt(s['valid_customers'])}**",
        f"- Valid invoices: {_fmt(s['valid_invoices'])}",
        f"- Valid product revenue: {_fmt(s['valid_revenue'])} GBP",
        f"- Cancellation lines kept in a separate table: {_fmt(s['cancellation_rows_kept'])} "
        f"(non-product cancellation lines dropped: {_fmt(s['cancellation_nonproduct_rows_dropped'])})",
        f"- Rows without CustomerID: {_fmt(s['anonymous_rows'])} ({s['anonymous_rows_share_pct']}% of raw rows; "
        f"positive line value {_fmt(s['anonymous_positive_line_value'])} GBP). Excluded from customer analysis only.",
        f"- Exact duplicate rows among valid rows: {_fmt(s['exact_duplicate_rows_in_valid'])}",
        f"- Invoices starting with a letter other than 'C': {s['non_c_alpha_invoices']} (handled by the price rule)",
        "",
        "## 4. Historical evaluation framework",
        "",
        f"- Eligible customers (>= 1 valid purchase on/before cutoff): **{_fmt(meta['eligible_customers'])}**",
        f"- Customers first seen after the cutoff (excluded, no history): {_fmt(meta['customers_first_seen_after_cutoff_excluded'])}",
        f"- Inactive in the window: {_fmt(meta['inactive_customers'])} "
        f"({meta['inactivity_rate'] * 100:.1f}%)",
        f"- Active in the window: {_fmt(meta['active_customers'])}",
        "",
        "Definitions:",
        "",
        f"- **Recency**: {meta['recency_definition']}.",
        f"- **Frequency**: {meta['frequency_definition']}.",
        f"- **Monetary**: {meta['monetary_definition']}.",
        f"- **Outcome**: {meta['outcome_definition']}.",
        "",
        "## 5. Interpretation warning",
        "",
        "The outcome is an operational inactivity proxy over one 90-day window that includes the "
        "autumn holiday peak. It is not proof that a customer permanently stopped buying, and the "
        "rate depends on the chosen cutoff.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description="Build ChurnGuard customer dataset")
    p.add_argument("--input", default=str(Path("data") / "raw" / "Online Retail.xlsx"))
    p.add_argument("--outdir", default=str(Path("data") / "processed"))
    p.add_argument("--cutoff", default=PipelineConfig.cutoff_date)
    p.add_argument("--window-days", type=int, default=PipelineConfig.window_days)
    p.add_argument("--drop-duplicates", action="store_true")
    args = p.parse_args(argv)

    config = PipelineConfig(cutoff_date=args.cutoff, window_days=args.window_days,
                            drop_duplicate_rows=args.drop_duplicates)
    print(f"Reading {args.input} (this can take about a minute) ...")
    raw = load_raw(args.input)
    result = clean_transactions(raw, config)
    table, meta = build_customer_table(result.valid, result.cancellations, config,
                                       result.data_start, result.data_end)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    table.to_csv(outdir / "customers_features.csv", index=False)
    audit_payload = {"config": config.to_dict(), "summary": result.summary,
                     "steps": result.audit, "framework": meta}
    (outdir / "data_audit.json").write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
    write_markdown_report(outdir / "data_audit.md", config, result, meta)

    print(f"Valid rows: {result.summary['valid_rows']:,} | valid customers: {result.summary['valid_customers']:,}")
    print(f"Eligible customers at cutoff {meta['cutoff_date']}: {meta['eligible_customers']:,} "
          f"| inactive rate: {meta['inactivity_rate'] * 100:.1f}%")
    print(f"Wrote {outdir / 'customers_features.csv'}, data_audit.json, data_audit.md")


if __name__ == "__main__":
    main()
