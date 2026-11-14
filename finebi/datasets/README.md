# Credit Portfolio Analytics - FineBI SQL Datasets

28 PostgreSQL SELECT datasets for five native FineBI pages. All data is synthetic. Report labels are English and the reporting currency is RUB.

## Create datasets

1. Use the existing `Credit Portfolio` folder and `CREDIT_PORTFOLIO` connection. The source is `127.0.0.1:55433 / credit_portfolio_demo`, schema `credit`. No new database objects are required.
2. Create one SQL dataset for each catalog entry, using the exact English dataset name. `Overview KPIs` already exists: edit that dataset rather than creating a duplicate.
3. Use **Direct** mode for parameterized datasets. Extracted data is evaluated at extraction time and will not implement interactive SQL parameter filtering. Switching the data-list view is not proof that a particular existing dataset has changed mode; check the dataset/workbook behavior.
4. Paste the contents of the matching SQL file. Each file is a separate query. The files deliberately have no trailing semicolon. `${INT(p_date_key)}` and similar expressions are FineBI macros; paste them unchanged into FineBI, not a PostgreSQL console.
5. Click parameter **Refresh**, set the parameters actually present in that query to **Number**, and enter the defaults below. FineBI may initially suggest Text and `1`; replace those defaults. Dictionary datasets have no parameters.
6. Click **Preview**, then save. After adding the datasets to the workbook, configure SQL parameter bindings on the dashboard filters. Identical parameter names alone do not bind components automatically.
7. Each SQL file is self-contained. Do not join the 28 result datasets together. Add them independently to the workbook and choose the corresponding dataset for each component.

Official FineBI references: [SQL dataset creation](https://help.fanruan.com/finebi6.X/doc-view-890.html), [SQL parameters](https://help.fanruan.com/finebi6.X/doc-view-471.html), [Direct data](https://help.fanruan.com/finebi6.X/doc-view-85.html), [Filter parameter bindings](https://help.fanruan.com/finebi6.X/doc-view-1905.html).

## Parameters

| Parameter | Filter label | Type | Default |
|---|---|---|---|
| `p_date_key` | As Of Month | Number | `20261031` |
| `p_product_id` | Product | Number | `0` |
| `p_region_id` | Region | Number | `0` |
| `p_channel_id` | Channel | Number | `0` |
| `p_min_dpd` | Minimum DPD | Number | `1` |
| `p_loan_id` | Loan ID | Number | `0` |

`p_date_key` is an integer month-end key, not a Date parameter. `0` selects all products/regions/channels. `p_min_dpd=1` selects past-due active contracts in the registry only. `p_loan_id=0` shows the intentional no-selection state; use `2170` to preview a populated Loan Details page, then restore `0` for production defaults.

## Dataset catalog

Create the five filter dictionaries first, then the page datasets in the order below.

| # | Page | FineBI dataset name | SQL file |
|---|---|---|---|
| 1 | Shared Filters | Filter - As Of Month | [filter_date.sql](sql/filter_date.sql) |
| 2 | Shared Filters | Filter - Product | [filter_product.sql](sql/filter_product.sql) |
| 3 | Shared Filters | Filter - Region | [filter_region.sql](sql/filter_region.sql) |
| 4 | Shared Filters | Filter - Channel | [filter_channel.sql](sql/filter_channel.sql) |
| 5 | Shared Filters | Filter - Minimum DPD | [filter_min_dpd.sql](sql/filter_min_dpd.sql) |
| 6 | Portfolio Overview | Overview KPIs | [overview_kpis.sql](sql/overview_kpis.sql) |
| 7 | Portfolio Overview | Portfolio Balance Trend | [balance_chart.sql](sql/balance_chart.sql) |
| 8 | Portfolio Overview | Delinquency Trend | [quality_chart.sql](sql/quality_chart.sql) |
| 9 | Portfolio Overview | Portfolio Product Composition | [product_chart.sql](sql/product_chart.sql) |
| 10 | Portfolio Overview | Regional Performance | [region_table.sql](sql/region_table.sql) |
| 11 | Sales and Funnel | Sales KPIs | [sales_kpis.sql](sql/sales_kpis.sql) |
| 12 | Sales and Funnel | Application Funnel | [sales_funnel_chart.sql](sql/sales_funnel_chart.sql) |
| 13 | Sales and Funnel | Disbursement Trend | [sales_trend_chart.sql](sql/sales_trend_chart.sql) |
| 14 | Sales and Funnel | Disbursements by Channel | [sales_channel_chart.sql](sql/sales_channel_chart.sql) |
| 15 | Sales and Funnel | Sales Plan vs Actual | [sales_plan_table.sql](sql/sales_plan_table.sql) |
| 16 | Sales and Funnel | Channel Funnel Performance | [sales_channel_table.sql](sql/sales_channel_table.sql) |
| 17 | Delinquency and Portfolio Quality | Portfolio Quality KPIs | [quality_kpis.sql](sql/quality_kpis.sql) |
| 18 | Delinquency and Portfolio Quality | DPD Bucket Exposure | [quality_buckets.sql](sql/quality_buckets.sql) |
| 19 | Delinquency and Portfolio Quality | DPD Transition Matrix | [quality_transitions.sql](sql/quality_transitions.sql) |
| 20 | Delinquency and Portfolio Quality | Loan Registry | [quality_registry.sql](sql/quality_registry.sql) |
| 21 | Vintage Analysis | Vintage KPIs | [vintage_kpis.sql](sql/vintage_kpis.sql) |
| 22 | Vintage Analysis | Vintage Matrix | [vintage_matrix.sql](sql/vintage_matrix.sql) |
| 23 | Vintage Analysis | Vintage Curves | [vintage_curves.sql](sql/vintage_curves.sql) |
| 24 | Loan Details | Loan Details KPIs | [loan_kpis.sql](sql/loan_kpis.sql) |
| 25 | Loan Details | Loan Balance History | [loan_balance_chart.sql](sql/loan_balance_chart.sql) |
| 26 | Loan Details | Loan DPD History | [loan_dpd_chart.sql](sql/loan_dpd_chart.sql) |
| 27 | Loan Details | Loan Operations | [loan_operations.sql](sql/loan_operations.sql) |
| 28 | Loan Details | Loan Payment Schedule | [loan_schedule.sql](sql/loan_schedule.sql) |

## Filter bindings

| Dictionary dataset | Display field | Value field | SQL parameter |
|---|---|---|---|
| Filter - As Of Month | label | id | p_date_key |
| Filter - Product | label | id | p_product_id |
| Filter - Region | label | id | p_region_id |
| Filter - Channel | label | id | p_channel_id |
| Filter - Minimum DPD | label | id | p_min_dpd |

Use single-value selections. Bind a filter to every relevant dataset's SQL parameter in the workbook; the manifest lists the exact parameters for each dataset. FineBI 6.0.16+ supports binding one filter to multiple SQL parameters. On an earlier build, use the supported per-component parameter bindings or upgrade before assuming a shared filter controls all datasets.

`Loan Registry.loan_id` is the drill-through value for `p_loan_id`. Carry the selected `p_date_key` and portfolio filter context with the jump. Loan Details queries deliberately use only Loan ID and date; product/region/channel must be preserved as navigation/return context, not applied again to the selected contract.

## Field use, aggregation and units

- KPI datasets return one row. Use numeric fields for calculations; use `*_label` fields for preformatted display. `MAX` is safe for displaying a precomputed KPI or ratio; do not sum ratios across groups.
- Portfolio trend, product composition and DPD bucket `value` fields are in **RUB bn**. Disbursement trend, channel chart and Loan Balance History `value` fields are in **RUB m**. Loan DPD History values are in **days**. Loan Details KPI and table monetary fields are raw **RUB**.
- `Delinquency Trend.value` and `Vintage Curves.value` are **percentage points**: `6.94` means `6.94%`. Display a numeric value with a literal `%` suffix; a formatter that multiplies fractions by 100 would overstate them.
- Fields named `*_ratio`, `transition_ratio`, `ever_ratio`, `ratio31`, `ratio91`, and `plan_attainment` are **fractions**: `0.0694` means `6.94%`. Use standard percentage formatting.
- Tables generally expose raw RUB amounts plus text labels. `Regional Performance.balance_label` is already expressed in RUB bn; `balance` is raw RUB.
- For the transition pivot, rows = `from_bucket`, columns = `to_bucket`, value = `MAX(transition_ratio)`, formatted as percent. Sort using `from_order` and `to_order`. Each row's `opening_loans` repeats across seven cells; never sum it across the row. `SUM(loan_count)` is a count, not a transition percentage.
- For the vintage pivot, rows = `cohort_month` (descending), columns = `mob` (ascending), value = `MAX(ever_ratio)`, formatted as percent. Keep NULL as blank or an em dash. Immature cohorts must not become zero. `original_loan_count` and `original_amount` repeat across 12 MOB cells; do not sum them across MOBs. Use `Vintage KPIs` for portfolio totals.
- Chronological charts must sort by `sort_date`, `month_end`, `snapshot_date`, `stage`, or `mob` as appropriate, rather than alphabetically by the formatted labels.
- Loan Registry, Loan Operations and Loan Payment Schedule return **all matching rows**. Use FineBI's native table pagination/scrolling and explicit sort fields (`registry_row_no` or `row_no`). The old FineReport eight-row limit and page parameters have been removed. SQL has no LIMIT; check component row limits separately. FineBI editor previews can show only part of a dataset.

## Preserved metric definitions

- Overview balance is end-of-day principal. MTD disbursements follow the loan issue/funding date.
- Sales funnel follows applications submitted during the selected month, with outcomes known by the selected cutoff. It is a different population from funded-date disbursements.
- Sales Plan vs Actual follows month, product and region and intentionally covers all channels, because the source plan has no channel allocation.
- 31+/91+ DPD exposure is the entire outstanding principal of affected loans. Minimum DPD changes only the registry and its displayed count, not headline quality metrics or transitions.
- Vintage keeps closed and written-off contracts in original cohort denominators. Only fully mature, fully observed cohort/MOB cells have a ratio. Pooled MOB KPIs are weighted by original loan counts, not an average of cohort percentages. The curves retain the four source-selected cohorts rather than all 24 series.
- Loan operations stop at the selected cutoff. The effective payment schedule may contain future due installments, but paid, written-off, cancellation and closure information is evaluated as of the cutoff.

## Quick acceptance checks

With `p_date_key=20261031` and product/region/channel all `0`: Overview balance should display **RUB 19.55 bn**, MTD disbursements **RUB 800.88 m**, active borrowers **7,573**, monthly growth **2.52%**, 31+ DPD **6.94%**, 91+ DPD **4.95%**. Vintage Matrix should return **288 rows** (24 cohorts x 12 MOBs). With `p_loan_id=2170`, Loan Payment Schedule should return **36 rows**, rather than the old first eight installments.

Use `validation.json` for database-side results and parameter-specific row counts. Database validation expands FineBI macros to numbers and executes read-only PostgreSQL SELECTs; it does not replace checking parameter bindings and rendered components inside FineBI.
