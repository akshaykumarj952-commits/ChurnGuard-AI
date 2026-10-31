# ChurnGuard data audit

Generated automatically by `churnguard.build_dataset`. Do not edit by hand.

Source: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33 (CC BY 4.0).

## 1. Settings used

- Cutoff date (inclusive): **2011-09-09**
- Observation window: **2011-09-10 to 2011-12-08** (90 days)
- Last complete day in the data: 2011-12-08 (file ends 2011-12-09 12:50:00; the final day is treated as incomplete)
- Duplicate rows dropped: False

## 2. Row-by-row exclusions (nothing is dropped silently)

| Step | Rule | Rows before | Removed | Rows after | Line value removed |
|---|---|---:|---:|---:|---:|
| 0_unparseable | InvoiceDate, Quantity or UnitPrice could not be read | 541,909 | 0 | 541,909 | 0.00 |
| 1_missing_customer_id | CustomerID is blank; transaction cannot be linked to a customer | 541,909 | 135,080 | 406,829 | 1,447,682.12 |
| 2_cancellations | InvoiceNo starts with 'C' (UCI: cancellation) | 406,829 | 8,905 | 397,924 | -611,342.09 |
| 3_non_positive_qty_or_price | Quantity <= 0 or UnitPrice <= 0 on a non-cancellation row | 397,924 | 40 | 397,884 | 0.00 |
| 4_non_product_codes | StockCode is a service/fee code, not a product: AMAZONFEE, B, BANK CHARGES, C2, CRUK, D, DOT, M, POST, S | 397,884 | 1,544 | 396,340 | 150,341.25 |
| 5_exact_duplicates | Reported only (not removed) | 396,340 | 0 | 396,340 | 0.00 |

Notes:

- **1_missing_customer_id**: Excluded from customer-level analysis only. Their size is reported in summary['anonymous_*'] so the exclusion is visible.
- **2_cancellations**: Moved to a separate table; never counted as a purchase.
- **3_non_positive_qty_or_price**: 0 rows with Quantity<=0, 40 rows with UnitPrice<=0 (a row can be in both).
- **4_non_product_codes**: Postage, carriage, manual entries, fees etc. are not product purchases.
- **5_exact_duplicates**: 5187 rows are exact duplicates of an earlier row. They may be genuine repeated scan lines, so they are kept by default (set drop_duplicate_rows=True to test sensitivity).

## 3. What remains after cleaning

- Raw rows: 541,909
- Valid purchase rows: **396,340**
- Customers with valid purchases: **4,334**
- Valid invoices: 18,402
- Valid product revenue: 8,761,066.65 GBP
- Cancellation lines kept in a separate table: 8,539 (non-product cancellation lines dropped: 366)
- Rows without CustomerID: 135,080 (24.93% of raw rows; positive line value 1,755,276.64 GBP). Excluded from customer analysis only.
- Exact duplicate rows among valid rows: 5,187
- Invoices starting with a letter other than 'C': 3 (handled by the price rule)

## 4. Historical evaluation framework

- Eligible customers (>= 1 valid purchase on/before cutoff): **3,368**
- Customers first seen after the cutoff (excluded, no history): 966
- Inactive in the window: 1,451 (43.1%)
- Active in the window: 1,917

Definitions:

- **Recency**: days from the customer's last valid purchase date to the cutoff date (0 = purchased on cutoff day).
- **Frequency**: number of distinct valid invoices on or before the cutoff.
- **Monetary**: sum of Quantity x UnitPrice over valid product lines on or before the cutoff (GBP).
- **Outcome**: outcome_inactive = 1 if the customer has no valid purchase in the observation window.

## 5. Interpretation warning

The outcome is an operational inactivity proxy over one 90-day window that includes the autumn holiday peak. It is not proof that a customer permanently stopped buying, and the rate depends on the chosen cutoff.
