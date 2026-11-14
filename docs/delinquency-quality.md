# Delinquency and Portfolio Quality

The third story in `CREDIT_PORTFOLIO/Portfolio_Overview.fvs` follows the established native layout. Its navigation tab is **Portfolio Quality**; its full title is **Delinquency and Portfolio Quality**.

## Scope and metrics

The four shared controls select a completed month end, product, origination region and acquisition channel. All money is RUB. Stocks are measured on the selected date; write-offs are principal extinguished during that selected calendar month.

| Card | Meaning |
|---|---|
| Overdue principal | Unpaid scheduled principal with a due date before the reporting date |
| Overdue interest | Unpaid earned scheduled interest with a due date before the reporting date |
| 31+ DPD exposure | Full principal balance of contracts at DPD >=31 / full portfolio balance |
| 91+ DPD exposure | Full principal balance of contracts at DPD >=91 / full portfolio balance |
| Past-due loans | Active contracts with positive principal and DPD >0 |
| Monthly write-offs | Principal WRITE_OFF operations during the selected month; not cash repayments |

The bucket chart includes all active principal across DPD 0, 1–30, 31–60, 61–90 and 91+, in RUB billions. It reconciles to the complete selected portfolio. Overdue principal is already part of full outstanding principal and must not be added to it again. DPD 31+/91+ are project definitions rather than regulatory NPL classifications.

## Monthly transitions

The matrix compares the same contracts at the previous and selected month end. New contracts issued during the destination month are excluded. Closed and Written Off are distinct states and retained in the opening population, including continuing zero-balance terminal contracts.

Each row label includes its opening contract count. A cell shows its share of that row and its contract count. Zero movement is displayed as **0%**; no opening denominator is a dash. Positive percentages are rounded to one decimal, so a very small positive share can show 0.0% with a nonzero count. Row percentages may not add to exactly 100% after rounding. Diagonal shading means unchanged state, not low risk or successful collection.

## Registry

The list contains active positive-principal contracts under the shared scope. **Registry threshold** offers All active (0), 1+ DPD, 31+ DPD and 91+ DPD; select it and press the common **Apply** button. This threshold affects the list only, never cards, bucket exposure or matrix denominators.

The registry shows eight contracts per page, sorted by DPD descending, principal descending and loan ID ascending. Previous/Next targets are bounded by the available page count. If filtering reduces the result size, an out-of-range requested page is clamped to the final valid page. Empty results use Page 1 of 1 and a clear explanatory note. Amount columns show full RUB with two decimals.

Six numeric parameters are retained by all navigation tabs:

| Parameter | Default | Purpose |
|---|---:|---|
| p_date_key | 20261031 | Shared calendar month-end key |
| p_product_id | 0 | Shared product ID; 0 All |
| p_region_id | 0 | Shared origination region ID; 0 All |
| p_channel_id | 0 | Shared channel ID; 0 All |
| p_min_dpd | 1 | Registry-only minimum DPD |
| p_quality_page | 1 | Registry-only requested page |

## Native datasets

| Dataset | Grain |
|---|---|
| quality_kpis | One row: global scope metrics, dates and registry pagination state |
| quality_buckets | Five ordered active DPD buckets, or no rows for an empty portfolio |
| quality_transitions | All 49 from/to cells with exact opening denominators |
| quality_registry | At most eight dated contracts on the bounded requested page |
| filter_min_dpd | Four threshold choices |

The SQL lives in `src/delinquency.py` and is added to the combined thirty-one-dataset manifest. Native text/rectangle components render the transition matrix and registry. `dashboard/quality_page.py` defines the layout; the base fixture and database access rights are unchanged.

Registry loan references are native drill-through links. Each passes its actual row loan ID and resets both detail table pages. **Back to registry** retains all portfolio filters, the threshold and registry page. See [Loan Details](loan-details.md).

## Validation

Eight real PostgreSQL tests independently verify snapshot and write-off sums, bucket reconciliation, complete opening cohorts, terminal states, threshold isolation, historical/scoped results, disjoint bounded pagination and empty input. Native report tests require five stories, every directed navigation target and eleven explicit retained parameters.

The third-page delivery audit verified repeated registry paging 1 → 2 → 1 → 2, the 91+ threshold (473 contracts, 60 pages), the historical August 2025 Auto Loan / Moscow / Online slice, all six directed navigation paths, preserved registry state, an empty region scope and last-page clamping. The historical slice contains one registry contract at 91+ DPD; page 2 correctly clamps to page 1. An oversized request clamps to page 159, whose Next target remains 159. No new browser console errors were recorded during this final audit.

During the initial session a repeated pager action failed before the platform required sign-in. Both pager labels now depend on their target-page dataset values, making their native compute dependencies explicit. The final authenticated audit reproduced the original action sequence successfully. See `validation/quality-tests.log`, `validation/preview-quality-*.txt`, `validation/preview-quality-navigation.json` and `validation/quality-delivery.json` for evidence. Vendor trial notices remain visible.


## Shared scrolling layout follow-up

The November 5 update adapts the remaining pages and common controls to desktop panes from 640 px wide. All original fields, dataset scopes and actions remain available. See [narrow desktop layout](narrow-pages.md) for the current frame and verification.


## Current desktop layout

The compact desktop composition has been restored. Charts sit side by side, KPI cards occupy one row, and records remain tabular. Readability fixes, filters, paging and navigation are preserved; see [desktop layout](desktop-layout.md). Earlier scrolling-layout notes describe a superseded revision.
