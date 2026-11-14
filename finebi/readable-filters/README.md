# Readable filters for FineBI 6.0

The original numeric dataset handoff remains in `../datasets`. This companion
pack accepts English dictionary labels as SQL parameters and preserves numeric
fallbacks. It changes parameter interpretation, not the analytical calculations.

Run `python3 finebi/prepare_readable_filters.py --verify` from the project root
to regenerate the pack and compare its results with the numeric pack. The check
uses the existing read-only database account. FineBI formula evaluation is also
checked through the native UI; the Python check is not a substitute for it.

## Installed state on 7 November 2026

These public datasets have been switched to label-aware SQL:

- Overview KPIs
- Portfolio Balance Trend
- Delinquency Trend
- Portfolio Product Composition
- Regional Performance
- Sales KPIs
- Application Funnel
- Disbursement Trend
- Disbursements by Channel
- Sales Plan vs Actual
- Channel Funnel Performance
- Portfolio Quality KPIs
- DPD Bucket Exposure
- DPD Transition Matrix
- Loan Registry
- Vintage KPIs
- Vintage Matrix
- Vintage Curves
- Loan Details KPIs
- Loan Balance History
- Loan DPD History
- Loan Operations
- Loan Payment Schedule

Global parameters present in those datasets use **Text**, with defaults:

| Parameter | Default |
| --- | --- |
| p_date_key | October 2026 |
| p_product_id | All Products |
| p_region_id | All Regions |
| p_channel_id | All Channels |

Sales Plan vs Actual has no Channel parameter because the plan covers all channels.
Other public datasets retain the original numeric SQL and parameter types.
Their prepared label-aware versions are available here for later pages.
`p_loan_id` remains Number. The two quality sources with `p_min_dpd` now use Text with default `1+ DPD`; its labels are All active, 1+ DPD, 31+ DPD and 91+ DPD, with numeric fallbacks preserved.

## Portfolio Overview

The native dashboard has six KPI cards, two line charts, product composition
and a detailed regional table. Desktop canvas: 1280 × 900, fit to width.
Four required single-selection text dropdowns use the corresponding Filter
dictionary `label` fields. Each dropdown binds its SQL parameter separately to
all five Overview sources. Filters recalculate immediately; no Apply button.
No joins between result datasets are required.

Native UI checks passed for default October 2026 and for August 2025 /
Personal Loan / Moscow / Online. The latter returned RUB 102.45 m balance,
RUB 6.66 m disbursements, 153 borrowers, +4.35% growth, 4.58% 31+ DPD and
1.39% 91+ DPD. Both trends and the regional table changed with the filters.
The default selections were restored. Six regional rows fit in the table.

The workbook editor was exited using its native Back button to release the
editing lock. A stale lock earlier in the session was cleared by signing out
and signing back in; closing the tab alone did not release it.

## Sales and Funnel and shared navigation

The existing report is now named Credit Portfolio Analytics and contains native
Overview and Sales and Funnel tabs under four shared filters. Sales contains
six KPI cards, a funnel, disbursement trend, channel disbursements, plan versus
actual and channel funnel performance tables. The size legend is hidden; the
funnel order is Submitted, Approved, Funded. English field aliases and units
are verified in the saved view.

Month, Product and Region bind all eleven installed sources. Channel binds ten
sources, excluding Sales Plan vs Actual, whose title states All Channels.
The note below Sales distinguishes submission cohorts (outcomes as of month
end) from loans selected by funding date. No joins are introduced.

Default Sales results: 1,654 applications, 45.41% approval, 43.41% approved to
funded, RUB 800.88 m funded, 400 loans, RUB 2.00 m average. The funnel is
1,654 / 751 / 326. August 2025 / Personal Loan / Moscow / Online returned
6 applications, 83.33% approval, 100.00% conversion, RUB 6.66 m funded,
6 loans and RUB 1.11 m average. Both tab directions retained all four filters
and matching Overview values. Defaults were restored and the saved view was
checked after leaving the editor with native Back. The temporary copied
report is explicitly named Overview Layout Backup and remains unpublished.

Evidence and component IDs: `../sales-build-state.json`.

## Delinquency and Portfolio Quality

The third native tab contains six summary cards, active principal by DPD bucket,
a seven-state transition matrix, and the complete loan registry. Shared filter
bindings now cover fifteen SQL sources (fourteen for Channel, excluding the
sales plan). The registry-only required threshold defaults to 1+ DPD; it binds
p_min_dpd only to Loan Registry. Summary populations and matrix denominators
therefore remain unchanged when that threshold changes.

The matrix uses a native Color Table with preformatted cell text, fixed 12px
black text and loan counts in tooltips. It preserves row shares and exact
counts, opening populations in row labels, zero movements and absent opening
denominators. Closed and Written Off remain distinct. Registry paging is
native FineBI: 100 matching rows per page with scrolling, rather than the old
eight-row FineReport pages. All nine English columns fit the desktop width.

Default and historical KPI results, 91+ threshold isolation, page 1/2/1,
valid empty registry selection and all six directed navigation edges among
three tabs were verified. See ../quality-build-state.json for component IDs,
control values, evidence and final save status.

## Vintage Analysis

The fourth native tab has six cards (original loans, funded amount, cohorts,
and pooled ever-31+ MOB 3/6/12), a full-width chronological matrix, cohort curves
and a methodology note. Native scrolling exposes all 24 cohorts and MOB 1–12;
FineReport-specific six-by-six pagination is not required here. MOB is a numeric
dimension using identical-value groups, not interval bins. Year Month grouping
keeps cohorts chronological. Matrix text is fixed 12px black, retaining observed
0.0% versus immature/unavailable dashes. Original loan counts are in tooltips.

Each fixed-age card has its own eligible cohort/loan population in its tooltip.
The visible note states that populations differ by age and that closed and
written-off contracts stay in original denominators. Curves use only observed
source-selected cohort/age points, already in percentage points; the vertical
axis starts at zero. No future points are filled.

All four required English shared controls now cover 18 SQL source parameters
(17 for Channel, excluding the all-channel plan). The eight Vintage widgets are
included in each control range. Default, historical and earliest immature slices
match source controls. All six new directed paths Vintage ↔ Overview/Sales/Quality
retain the historical four-filter selection; the Quality-only registry threshold
also survives a Vintage round trip. Defaults were restored.

The saved view was checked after native Back released the editor lock; the
temporary viewport override was reset. Evidence and final save status:
`../vintage-build-state.json`.

## Loan Details

The fifth tab contains the selected contract, six indicators, contract terms,
balance and DPD history, dated operations and all schedule installments. The
five detail datasets accept the shared month and numeric `p_loan_id`. Product,
region and channel remain part of the portfolio context.

The native registry Jump uses `loan_details_url` for the clicked row and opens
the authenticated report preview in a full-screen dialog. It passes the four
shared selections and the registry threshold. The report is saved with Loan
Details as the active tab for the Jump destination. The dialog can be closed to
return to the existing registry. The numeric SQL handoff is still portable.

Verified the two August 2025 contracts under Personal Loan / Moscow / Online /
91+ DPD, a standard October 2026 contract in the saved report, and the empty
state when opening the tab without a selection. A full five-tab regression audit
is separate from the Loan Details delivery checks.
