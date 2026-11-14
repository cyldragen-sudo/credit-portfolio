# Vintage Analysis

[Open the fourth story](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=4).

The native FineVIS page compares cumulative delinquency among monthly origination cohorts at equal months on book (MOB). It uses the same English visual style, protected SELECT-only PostgreSQL connection and shared controls as the other three stories. All records are synthetic.

## Population and observations

Cohorts include loans issued from the fixed report start, **November 1, 2024**, through the selected month end. Product, region and channel refer to origination dimensions. Earlier loans remain part of the overall portfolio but are outside this vintage window. The default view therefore contains **8,759 original loans in 24 cohorts**, rather than all 12,000 fixture loans.

MOB means a completed monthly anniversary of each contract's issue date, clamped to the end of the destination month. A January 31 issue reaches MOB 1 on February 28 or 29. Each cohort cell waits until every contract in the filtered cohort has reached that age. Changing the segment can therefore change the maturity date.

The numerator counts original contracts that ever reached DPD 31 or more by their own anniversary. The denominator is all original contracts in that cohort. Closed and written-off loans remain in the denominator. Future observations are excluded. This is cumulative-ever delinquency by contract count; it is not current balance exposure or a lifetime loss estimate.

## Page contents

| Component | Meaning |
|---|---|
| Original loans | All original contracts in the selected origination window and scope |
| Original funded amount | Sum of their original principal, in RUB |
| Origination cohorts | Number of nonempty monthly origination cohorts |
| Ever 31+ · MOB 3 / 6 / 12 | Pooled cumulative-ever count divided by original contracts, using only fully mature and available cohorts at that exact age |
| Cohort matrix | Six monthly cohorts × six ages per block; bounded pages and a MOB 1–6/7–12 selector cover all 24 cohorts and 12 ages |
| Cohort curves | Up to four cohorts, sampled every sixth nonempty cohort oldest first, with observed MOB points only |

Fixed-age card notes show the eligible cohort and contract counts. Eligible populations differ by age, so the three cards are not one common-population time series. At the default cutoff they show **1.12% at MOB 3**, **11.72% at MOB 6** and **18.50% at MOB 12**, with 21 / 18 / 12 eligible cohorts respectively.

Matrix dashes represent immature or unavailable cells. Measured zero is displayed as `0.0%`; a nonzero fraction can also round to `0.0%`. The matrix has alternating row shading for reading, without numeric heatmap thresholds. Empty scopes display zero population, dash rates, an empty matrix/chart and a clear explanation. The larger paged grid is verified on desktop panes from640px wide. See [readability verification](vintage-readable.md).

## Controls and navigation

Select **As of**, **Product**, **Region** and **Channel**, then press **Apply**. The five tabs connect all stories and explicitly retain `p_date_key`, `p_product_id`, `p_region_id`, `p_channel_id`, `p_min_dpd` and `p_quality_page`. The last two parameters affect only Portfolio Quality's registry. The selected loan and its two detail page parameters are also retained for Loan Details. The view adds `p_vintage_page` and `p_vintage_mob_start`, retained across all tabs. Choose the age range and press Apply; Previous/Next changes the cohort block.

FineVIS changes `page_number` in the URL during navigation. Applied selections are kept in the report session; bookmark an explicit numeric parameter URL to restore a precise slice after reload. For example, append `&p_date_key=20250831&p_product_id=2&p_region_id=1&p_channel_id=2` to the fourth-story URL.

## Datasets and implementation

| Dataset | Grain and scope |
|---|---|
| vintage_kpis | One row with original totals, fixed-age rates and eligible denominators |
| vintage_matrix | One monthly cohort × MOB 1–12 cell, including immature cells with NULL ratios |
| vintage_matrix_view | At most 36 visible cells, selected in SQL from the full matrix with bounded cohort/age context |
| filter_vintage_mob | Two age-block choices:1 and 7 |
| vintage_curves | One observed selected cohort × MOB point; percentages in chart units |

`src/vintage.py` reads existing `credit.v_loan_dimension`, `credit.loan_month_age` and reporting bounds. `dashboard/vintage_page.py` renders the native text matrix and native line chart. `src/overview.py` writes the combined31-dataset manifest. The native report has five stories, 784 widgets and ten charts. No fixture, schema, access-right or credential changes are required.

## Validation

Seven new real PostgreSQL tests cover original denominators, anniversary maturity, default and historical filters, pooled fixed-age ratios, monotonic observed curves, terminal loans, empty scopes and numeric validation. The full project suite is recorded in `validation/vintage-tests.log`. Native tests now require all twenty common navigation paths with eleven explicit parameters.

The fourth-page delivery audit verified the default view, all four dropdown controls, August 2025 / Auto Loan / Moscow / Online (31 contracts in ten cohorts), all twelve navigation paths, a retained 91+ registry threshold and page 2, empty scope, the initial November 2024 cohort with no mature MOB points, and reload from an explicit date URL. No new console errors were recorded. The original trial notice remains visible.

A fresh source reviewer found no Critical/Important issues, reran the seven SQL tests and native test, and independently reconciled 120 historical filtered cells, including 45 observed cells, to daily DPD snapshots. Minor future coverage opportunities are dedicated historical-ever assertions and a deeper native curve-style assertion; current SQL, source review and rendered checks cover the delivered behavior.

See `validation/vintage-delivery.json`, `validation/preview-vintage-*.txt`, `validation/preview-vintage-navigation.json` and `docs/screenshots/vintage-*.jpg`.


The shared [narrow desktop layout](narrow-pages.md) now stacks sections vertically and enlarges controls on all five stories; the Vintage six-by-six view and its data logic remain unchanged.


## Current desktop layout

The compact desktop composition has been restored. Charts sit side by side, KPI cards occupy one row, and records remain tabular. Readability fixes, filters, paging and navigation are preserved; see [desktop layout](desktop-layout.md). Earlier scrolling-layout notes describe a superseded revision.
