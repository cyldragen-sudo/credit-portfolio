# FineBI workbook and semantic layer

## Import the workbook

[Download Credit-Portfolio-Analytics.zip](migration/Credit-Portfolio-Analytics.zip). The export was created in FineBI **6.0.27** (platform build **11.5.12**) using Resource Migration. It contains one dashboard with five tabs, 50 components, and 28 Direct SQL datasets with their workbook dataset definitions. The SQL sources reference the connection name `CREDIT_PORTFOLIO`.

1. [Load the synthetic PostgreSQL database](../README.md#start-here). In the target FineBI instance, configure and test a PostgreSQL connection named `CREDIT_PORTFOLIO` with a read-only role. Enter the connection settings and credentials on that instance.
2. Use a matching FineBI version with Resource Migration enabled. As an administrator, open **System Management → Intelligent O&M → Resource Migration → Resource Import**. Upload the ZIP as downloaded. Review the resource list and assign the project to the target owner if FineBI prompts for an owner mapping. Select the dashboard and all its dependencies, then import. [FineBI Resource Migration documentation](https://help.fanruan.com/finebi-en/doc-view-4441.html)
3. Open **Credit Portfolio Analytics** under the chosen owner's **My Analysis**. Check all five tabs and confirm that month, product, region and channel stay selected when switching tabs.
4. The Loan Registry generates its drill-through URL in SQL. Its exported preview URL points to the source instance on `localhost:37799`. If the target preview URL differs, open the imported dashboard with **Loan Details** active, copy its authenticated preview URL, and replace the prefix before `?p_loan_id=` in the **Loan Registry** SQL dataset. Keep the URL parameter expressions and the component's Jump binding to `loan_details_url`. Open two different contracts from the registry and confirm the contract ID and reporting month in the dialog.

The ZIP contents were checked against the dashboard tabs and SQL catalog. A clean-instance import is pending verification. SHA-256 is `6c9460fcd05fe0acc11117f5215941f35d21040cb49f23e6fa08b00368e04222`.

## Recreate the workbook

1. Load the synthetic PostgreSQL database using the [repository setup](../README.md#start-here). In FineBI, configure a PostgreSQL data connection named `CREDIT_PORTFOLIO` with a read-only role and create a `Credit Portfolio` dataset folder.
2. Register the 28 SQL datasets using the names, SQL files, types and defaults in the [label-aware catalog](readable-filters/datasets.json). Use Direct mode. The five filter dictionaries have no parameters. The [dataset catalog](datasets/README.md#dataset-catalog) groups sources by tab and explains their units. The numeric pack provides the same business calculations with numeric filter keys.
3. Add the 28 datasets to one workbook. Build one desktop dashboard with five tabs, using the component mapping below. Use dataset-provided display fields for KPI cards and exact numbers for tables and charts.
4. Place four required single-select controls above the tab component. Use the `label` field from the corresponding dictionary and bind each control to every SQL parameter of its name in the [catalog](readable-filters/datasets.json). Put **Registry Threshold** in the quality tab and bind `p_min_dpd` only to **Loan Registry**.
5. Open the saved dashboard preview with Loan Details active and copy its authenticated preview URL. In `readable-filters/sql/quality_registry.sql`, replace the local preview URL before `?p_loan_id=` with the URL from your installation. Refresh the Loan Registry source in the workbook so it exposes `loan_details_url`. In the registry component's Jump settings, select a web link, insert `loan_details_url` from the dataset and use a full-screen dialog. Keep Loan Details selected as the saved preview's opening tab. Verify the jump from two rows and close the dialog to check the return context.

## Semantic layer

```mermaid
flowchart LR
    A[Applications and dated events] --> S[Sales and Funnel]
    L[Loan and origination dimensions] --> O[Overview]
    L --> S
    T[Month-end loan snapshots] --> O
    T --> Q[Delinquency and Portfolio Quality]
    V[Loan age observations] --> M[Vintage Analysis]
    L --> M
    P[Sales plan by month, product and branch] --> S
    Q -->|Loan ID and cutoff| D[Loan Details]
    T --> D
    E[Operations, installments and allocations] --> D
```

The [physical model and ER diagram](../docs/data-dictionary.md) show relational keys and grain. PostgreSQL [reporting views](../database/003_views.sql) add origination attributes and normalized facts. FineBI queries aggregate each fact at the grain below. Register the result datasets independently to preserve their denominators and avoid multiplying one-to-many rows. See the [metric contract](../docs/metrics.md) for formulas and reporting boundaries.

| Tab | Results and grain | Component and filter rules |
| --- | --- | --- |
| Overview | One KPI row per selection, one point per month/series, one row per product or region | Six cards, two lines, product donut, region table. Stocks use month-end principal, including overdue principal. Distinct borrowers cannot be added across regions or products. |
| Sales and Funnel | One KPI row, one value per funnel stage, funding by month or channel, one plan row per product, one funnel row per channel | Six cards, funnel, line, bars and two tables. Funnel counts applications submitted in the month with outcomes known at the cutoff. Funded-date disbursements use the issue date. Plan vs Actual covers all channels by design. |
| Delinquency and Portfolio Quality | One KPI row, one total per DPD bucket, one matrix cell per opening/closing bucket pair, one registry row per eligible contract | Six cards, DPD bars, color table and detailed registry. Matrix rates use the opening contract count, excluding new issues. Registry Threshold affects only the registry. |
| Vintage Analysis | One KPI row, one cell per origination cohort and MOB, one observed point per selected cohort and MOB | Six cards, color table and line chart. Sort cohort months chronologically and MOB numerically. Display `cell_label` so immature/unavailable cells show a dash. MOB rates use the original contracts from cohorts eligible at each age. |
| Loan Details | One selected contract at cutoff, one point per month-end, one row per operation or installment | Contract identity, six cards, terms, two lines and two tables. The loan ID and month select the contract. Product, region, channel and DPD threshold preserve portfolio context. Operations and payment allocations stop at the cutoff. Future installments can appear if their schedule was already effective. |

`Delinquency Trend.value` and `Vintage Curves.value` are percentage points. Fields such as `ever_ratio` and `transition_ratio` are fractions. Use the units recorded in the [field guide](datasets/README.md#field-use-aggregation-and-units) for amounts, ratios and chart axes.

## Verify

The October 2026 default shows RUB 19.55 bn in principal, RUB 800.88 m in disbursements, 7,573 active borrowers and 1,268 past-due contracts. The historical slice August 2025 / Personal Loan / Moscow / Online with 91+ DPD yields LN-0011359 and LN-0010387 in the registry. Inspect [the recorded browser checks](../validation/finebi-browser-checks.json) and [SQL parity results](readable-filters/validation.json).
