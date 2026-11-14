# FineReport page and dataset mapping

Create a PostgreSQL connection named **CREDIT_PORTFOLIO** for the portable report. Portfolio Overview, Sales and Funnel, Delinquency and Portfolio Quality, Vintage Analysis, and Loan Details are built as five stories in one locally deployed native report; see [local overview](local-overview.md). The files under `queries/` remain the five-page dataset definitions. The report uses thirty-one derived datasets under `dashboard/sql/` with a numeric month-end parameter contract: ten overview/shared datasets, six sales datasets, five quality datasets, five vintage datasets and five loan-detail datasets. PostgreSQL schema `credit` is explicit, so no search-path setting is needed.

| Page | Dataset files | Intended presentation |
|---|---|---|
| Portfolio Overview | 01 overview KPIs; 02 monthly trend; 03 breakdown | KPI cards, portfolio/quality lines, product and region table |
| Sales and Funnel | 04 funnel; 05 actual sales; 06 monthly plan | Submission-cohort funnel, funded-date sales comparison, plan/actual table |
| Delinquency and Portfolio Quality | 07 buckets; 08 transitions; 09 loan registry | Exposure and overdue amounts, count-based transition matrix, paged detail registry |
| Vintage Analysis | 10 vintage | Cohort-month × MOB matrix, original counts and ever-31+ curves |
| Loan Details | 11 header; 12 operations; 13 schedule; 14 history | Contract attributes, receipts versus write-offs, schedule reconciliation, balance/DPD history |
| Shared controls | 15 filter options | English product/channel/region choices, including ID 0 for All |

## Source SQL parameters

Use the `${parameter_name}` macros exactly as provided in the SQL files. Configure date pickers for dates and numeric single-select controls for IDs; display English labels while passing numeric IDs.

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| p_as_of | Date formatted YYYY-MM-DD | 2026-10-31 | State and outcome observation cutoff |
| p_start | Date formatted YYYY-MM-DD | 2024-11-01 | Beginning of flow, application cohort, vintage issue window, or displayed history |
| p_end | Date formatted YYYY-MM-DD | 2026-10-31 | End of flow/cohort window |
| p_product_id | Nonnegative integer | 0 | 0 All; 1 Personal Loan; 2 Auto Loan; 3 Mortgage |
| p_channel_id | Nonnegative integer | 0 | 0 All; 1 Branch; 2 Online; 3 Mobile App; 4 Partner |
| p_region_id | Nonnegative integer | 0 | 0 All; region IDs from query 15 |
| p_risk_id | Nonnegative integer | 0 | Vintage only: 0 All; 1 Low; 2 Medium; 3 High at origination |
| p_loan_id | Positive integer | 1 | Selected loan, passed from registry or breakdown navigation |
| p_min_dpd | Nonnegative integer | 0 | Registry minimum delinquency; 31 or 91 makes useful presets |
| p_offset | Nonnegative integer | 0 | Registry offset, in increments of 200 |

Enforce `2024-11-01 <= p_as_of <= 2026-10-31` and `p_start <= p_end <= p_as_of`. SQL caps outcomes at the as-of date, but the UI should reject conflicting date inputs. For earlier origination vintages, p_start may be as early as 2023-11-01; daily loan history still begins at the stored baseline.

The SQL macros perform text substitution, not prepared binding. Validate dates and integer parameters on the server/runtime, not merely with client-side controls, and use the SELECT-only reporting account. `src/query_contract.py` validates local verification inputs; it does not automatically validate a deployed FineReport page. Do not accept free-form strings for these controls.

## Interaction rules

- Preserve the as-of date and product/channel/region scope when drilling to another aggregate page.
- Pass `p_loan_id` and `p_as_of` when opening Loan Details. The card describes that contract, independent of the source page's aggregate filters.
- Reset `p_offset` to zero when registry filters change. Each registry response contains at most 200 rows.
- The plan dataset has no channel parameter because its source targets have no channel dimension. Label it **All Channels — Monthly Plan**, and avoid implying a selected-channel target.
- End-date and start-date controls have different meanings across pages; label them **Submitted Between**, **Funded Between**, or **Origination Cohorts** as appropriate.
- Overview cards use the as-of date and month-to-date funding; their trend uses completed month ends from p_start. The comparison is against the previous calendar month end.
- Display NULL ratios as a dash. Display absent vintage cells as blank. A returned vintage zero is a mature cohort with no observed 31+ event.
- Format monetary values with RUB units and separators. Fractions use percentage formatting; annual contract rates use ordinary numeric formatting plus a percent sign.

The CSV samples under `data/page-samples` use defaults, including loan ID 1. The registry sample is capped at 200 rows; these extracts do not replace the full relational fixture.

The deployed native report uses numeric month-end `p_date_key` and bounded page parameters rather than the raw date/offset contract above. It retains all eleven values across tabs; see [local controls](local-overview.md#filters-and-metrics) and [loan parameters](loan-details.md#scope-and-parameters).

Native drill-through is described in the [FineReport documentation](https://help.fanruan.com/finereport-en/doc-view-311.html). All five deployed pages, JDBC datasets, shared filters and historical cutoffs have been tested in Preview. The prior four-page delivery exercised all twelve directions; the current delivery exercised the eight directions connecting Loan Details and tests all twenty common navigation bindings. Navigation also preserves the quality registry threshold and requested page. Sales uses the selected calendar month for both funded-date flows and the separate submission cohort. Its plan table always uses all channels; see [Sales and Funnel](sales-and-funnel.md). The quality page uses same-contract opening cohorts, dated write-offs and a bounded eight-contract registry; see [quality definitions](delinquency-quality.md). The vintage page displays a readable6×6block covering all24cohorts / MOB1–12via paging and age selection, original cohort counts, pooled mature fixed-age cards and observed curves; see [vintage definitions](vintage-analysis.md). Loan Details opens the actual selected registry ID and restores its saved return context, with dated contract data and full paged tables; see [loan definitions](loan-details.md).
