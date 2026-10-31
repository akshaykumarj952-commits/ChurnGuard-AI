"""Central, transparent settings for the historical evaluation framework.

Every number that changes the scientific result lives here, so it can be
reported on the poster and changed without editing the logic.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

# Stock codes that are NOT products. Each one was checked against its own
# Description in the UCI Online Retail file (see docs in data_audit.md).
NON_PRODUCT_CODES = (
    "POST",          # POSTAGE
    "DOT",           # DOTCOM POSTAGE
    "M",             # Manual (manual entry; the lower-case 'm' is upper-cased)
    "C2",            # CARRIAGE
    "BANK CHARGES",  # Bank Charges
    "D",             # Discount
    "S",             # SAMPLES
    "AMAZONFEE",     # AMAZON FEE
    "CRUK",          # CRUK Commission
    "B",             # Adjust bad debt
)


@dataclass(frozen=True)
class PipelineConfig:
    """Settings for cleaning, feature building and outcome labelling.

    cutoff_date:  last day (inclusive) whose transactions may be used to build
                  customer features. Everything after it is "the future".
    window_days:  length of the observation window that starts the day after
                  the cutoff. A customer is 'inactive' if they make no valid
                  purchase inside it.
    """

    cutoff_date: str = "2011-09-09"
    window_days: int = 90
    non_product_codes: tuple = NON_PRODUCT_CODES
    drop_duplicate_rows: bool = False  # default: keep, but report the count

    def to_dict(self) -> dict:
        d = asdict(self)
        d["non_product_codes"] = list(self.non_product_codes)
        return d
