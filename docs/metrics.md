# Metric contract

All money is RUB, stored as exact two-decimal PostgreSQL NUMERIC. Generator arithmetic uses integer kopecks. Report ratios are fractions between zero and one, formatted as percentages by FineReport. Contract annual interest rates are already percent values, such as 17.9; do not apply percentage multiplication again.

## Portfolio and growth

| Metric | Definition and denominator | Decision supported |
|---|---|---|
| Portfolio balance | Sum of outstanding principal at one end-of-day date, including overdue principal | Size and product/region allocation |
| Balance change | Current balance minus previous calendar month-end balance | Growth investigation |
| Balance change ratio | Balance change / previous month-end balance; NULL if baseline is zero | Comparable growth |
| Active loans | Contracts with principal balance > 0 on the selected date | Exposure population |
| Active borrowers | Distinct customer IDs among active loans in the entire selected scope | Borrower reach; do not sum product/region distinct counts |
| Disbursements | Original principal of loans funded in the selected date range; Overview uses month-to-date | Sales volume; a flow, not a stock |
| 31+ exposure ratio | Full outstanding principal of contracts with DPD >=31 / full portfolio principal | Early quality guardrail |
| 91+ exposure ratio | Full outstanding principal of contracts with DPD >=91 / full portfolio principal | Severe delinquency guardrail |
| Overdue principal | Unpaid scheduled principal whose due date is strictly before the report date | Amount currently past due |
| Overdue interest | Unpaid earned scheduled interest whose due date is strictly before the report date | Interest collection backlog |

Never add balances across dates, add overdue principal to a balance that already contains it, or average percentage rows without their denominators. Use SUM(numerator)/SUM(denominator). 31+ and 91+ are project definitions, not regulatory NPL classifications.

## Delinquency

DPD is the number of calendar days since the oldest unpaid principal or interest obligation. An unpaid obligation due today is DPD 0; tomorrow it is DPD 1. Bucket boundaries are 0, 1–30, 31–60, 61–90, and 91+. Penalties and payment holidays are not modeled.

The full principal of a contract with DPD 45 enters the 31+ exposure numerator, even if only a small installment is overdue. Closed and written-off contracts have zero current principal and DPD 0 but retain their earlier `ever_31_plus` flag.

Monthly transitions compare the same contracts at consecutive calendar month ends. The denominator of each matrix row is the number of contracts in its opening bucket. New loans issued during the destination month are excluded. Closed and Written Off are explicit states, including their continuing zero-balance histories. The latest matrix ends at the last completed month end on or before the as-of date.

## Sales and funnel

The funnel population is applications **submitted** between start and end, capped by the as-of date. Approval and funding outcomes may occur after that submission window but must occur by the as-of date. Approved applications include approved cases later withdrawn.

- Approval ratio = approved applications / submitted applications.
- Approved-to-funded ratio = funded applications / approved applications.
- In progress = neither funded nor terminally declined/withdrawn by the as-of date.
- Average days to funding = arithmetic mean of funded date minus submission date among funded cohort applications.
- Average funded amount = funded amount / funded contracts for the funded-date flow.
- Original-amount-weighted rate = SUM(original principal × annual percent rate) / SUM(original principal).
- Plan attainment = actual funding amount / planned amount at month/product/branch grain. Monthly targets are not prorated; in an incomplete month actual is to date. No channel target exists. Range endpoints select whole plan months.

When the denominator is zero, return NULL and display a dash, not a zero rate. A recent application cohort has incomplete outcomes. Synthetic plans demonstrate comparisons and are not business-approved targets.

## Vintage

Cohort month is the calendar month of origination. Months on book (MOB) is the completed monthly anniversary of each loan, preserving its original day and clamping to month end. For example, January 31 + one month is February 28 or 29.

For cohort C and MOB m:

`ever_31_plus_ratio = original contracts that reached DPD >=31 by their m-th anniversary / original contracts in C`.

Keep repaid and written-off loans in the original denominator. A cell is emitted only when **every contract in the selected cohort** has reached that anniversary by the as-of date. Absence means immature or no cohort, not zero delinquency. Each observation uses only information available through its own anniversary.

This is an original-count, cumulative-ever metric; it is not a current balance metric or lifetime loss estimate. Segment selection can change both cohort size and latest issue date; maturity is therefore recomputed after filtering.

## Cadence and thresholds

Daily review: balances and arrears. Monthly review: sales targets, transitions and vintage quality. No red/amber business thresholds are asserted without a baseline and business owner. Add demonstration thresholds only with an explicit Demo label. Growth and sales should always be reviewed alongside quality; a shrinking 91+ ratio after write-offs is not automatically a recovery in collections.
