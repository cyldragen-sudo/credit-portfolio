# Sales and Funnel

The second native story in `CREDIT_PORTFOLIO/Portfolio_Overview.fvs` uses the same four controls and style as Portfolio Overview. Switch stories using the top tabs; the applied month, product, origination region and acquisition channel are passed explicitly in both directions.

## Two populations

**Funded-date sales:** loans funded from the first day of the selected month through its month end. This population supplies disbursement amount, funded contracts, average funded amount, the disbursement trend and channel volume chart. It matches Overview's month-to-date disbursement value for the same cutoff and filters.

**Application submission cohort:** applications submitted during the selected month, with approval, funding and terminal outcomes observed only by its month end. Some loans funded this month came from earlier applications; some applications submitted this month will be funded later. The funnel-funded count therefore need not equal funded-date sales.

## KPI cards and funnel

| KPI | Definition |
|---|---|
| Disbursements | Sum of original principal funded during the month |
| Funded loans | Count of contracts funded during the month |
| Avg funded amount | Funded amount / funded contracts; dash for no contracts |
| Applications | Number submitted during the month |
| Approval rate | Cohort applications approved by cutoff / submitted applications |
| Approved to funded | Cohort applications funded by cutoff / cohort applications approved by cutoff |

The native funnel shows Submitted, Approved and Funded stages with exact counts below it. The accompanying summary shows declined, withdrawn and in-progress applications, plus the average elapsed calendar days from submission to funding among funded cohort applications. Approved applications that were later withdrawn remain in the approval stage. Ratios with no denominator show a dash.

The monthly trend starts in November 2024 and ends at the selected month; missing flow months within a nonempty scope show zero, while a wholly empty scope clears the chart. Channel conversion rows use the submission cohort and display submitted count, approval rate, funded/approved rate and average funding days.

## Monthly plan versus actual

The **ALL CHANNELS** table aggregates the original month/product/branch targets to product rows within the selected origination region. Actuals are funded-date volumes in the same month/product/region across all channels. Amount columns are RUB millions, and attainment is SUM(actual)/SUM(plan).

The channel filter does not affect this table because no channel targets exist. This is explicitly labeled in the page. For example, Auto Loan/Moscow/Partner in August 2025 shows selected-channel funding of RUB 5.35 m, while the all-channel product plan table shows RUB 33.05 m actual funding against RUB 33.69 m plan. These amounts refer to different declared scopes.

## Native datasets

| Dataset | Purpose |
|---|---|
| sales_kpis | Single-row flows, cohort counts, rates and English display labels |
| sales_funnel_chart | Three ordered submission-cohort stages |
| sales_trend_chart | Month-end funded-date volume series in RUB millions |
| sales_channel_chart | Selected-month funded volume by channel |
| sales_plan_table | Product-level all-channel target/actual comparison |
| sales_channel_table | Submission-cohort conversion by channel |

`src/sales.py` builds these projections without changing base data. `src/overview.py` writes the combined thirty-one-dataset manifest, including the quality, vintage and loan-detail stories; `PortfolioDatasets.java` serializes both portable named and protected local connections. Numeric macro validation, date calendar restrictions, installation backups and credential exclusion remain in effect.

Recent cohorts can have many applications still in progress. The scenario probabilities and targets are synthetic demonstrations, not underwriting advice, forecasts or operational commitments.


## Shared scrolling layout follow-up

The November 5 update adapts the remaining pages and common controls to desktop panes from 640 px wide. All original fields, dataset scopes and actions remain available. See [narrow desktop layout](narrow-pages.md) for the current frame and verification.


## Current desktop layout

The compact desktop composition has been restored. Charts sit side by side, KPI cards occupy one row, and records remain tabular. Readability fixes, filters, paging and navigation are preserved; see [desktop layout](desktop-layout.md). Earlier scrolling-layout notes describe a superseded revision.
