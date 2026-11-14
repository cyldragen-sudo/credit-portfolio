# Native FineBI Migration

The user requested moving the credit report to local FineBI and supplied access. Preserve the five analytical jobs, English product UI, synthetic data, metric definitions and practical shared filters. Use native FineBI datasets/charts/dashboards. The existing FineReport report remains available.

## Implementation

- [x] Inspect FineBI and create a named workbook shell.
- [x] Configure and test CREDIT_PORTFOLIO using the existing SELECT-only reporting role.
- [x] Add all 28 manually created direct SQL datasets to the workbook; bind the five Overview sources to native filters.
- [x] Build Portfolio Overview in the workbook; verify default and historical data and all four filters.
- [x] Build Sales and Funnel with native shared tabs and filters; validate default and historical data and both navigation directions.
- [x] Build Delinquency and Portfolio Quality with shared native tab navigation, registry threshold, matrix and registry validation.
- [ ] Build Vintage and Loan Details with native navigation/drill-through.
- [ ] Validate all five pages and retained state, save project/evidence and delivery links.

## Known platform facts

FineBI6 supports direct SQL datasets with formula macros and SQL parameter bindings; one filter can bind multiple SQL parameters in6.0.16+. Confirm the installed UI behavior before depending on it. Native paging can replace report-side record pagination where it preserves the intended population and drill return behavior.

Official references: https://help.fanruan.com/finebi6.X/doc-view-1905.html ; https://help.fanruan.com/finebi6.X/doc-view-890.html ; https://help.fanruan.com/finebi6.X/doc-view-471.html

## Evidence

Workbook ID55f29d3962924a6692b2b3816cdafda6, named Credit Portfolio Analytics. Local migration metadata is in finebi/migration.json. No credentials are stored in project delivery artifacts.

Portfolio Overview report ID: f1e20436263842bb85acb6f4f88cb775.
Native construction includes ten analytical components, four required English
dropdowns, and an English heading. Desktop 1280 × 900 with fit to width.
English label macros are installed for five Overview and six Sales sources.
The report is now Credit Portfolio Analytics with native Overview and Sales and
Funnel tabs, four shared filters and eleven Sales components. Native UI checks
passed for default and August 2025 / Personal Loan / Moscow / Online. Both
navigation directions retained filters and matching KPIs. Plan intentionally
covers all channels. Saved view checked outside editor; native Back released
the lock, viewport override reset, defaults restored. The unpublished copied
report is clearly named Overview Layout Backup. See finebi/sales-build-state.json
for component IDs, control values and screenshots. Quality was subsequently completed; see 2026-11-07-finebi-quality.md and finebi/quality-build-state.json. Vintage, Loan Details and full five-page validation remain pending.
