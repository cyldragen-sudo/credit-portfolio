# Readable Vintage matrix

This document records the November 4 matrix change. The current report uses the restored [compact desktop layout](desktop-layout.md), retaining this six-by-six matrix and its paging/data contract.

[Open a mature block](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=4&p_vintage_page=3&p_vintage_mob_start=7).

The Vintage matrix now shows **six monthly cohorts × six MOB ages per block**, with 38-design-pixel values and larger cohort labels. Previous/Next changes the cohort block. Select **MOB 1–6** or **MOB 7–12**, then press **Apply**. The current cohort range and total are displayed below the grid. All 24 cohorts and 12 ages remain available; KPI cards, original denominators, maturity rules and cohort curves are unchanged.

That revision preserved the existing native FineVIS canvas, header, six cards and right-hand curve/guide panels. The later shared scrolling layout stacks these sections vertically. The [vendor canvas documentation](https://help.fanruan.com/finereport-en/doc-view-8685.html) confirms that adaptation applies to all template pages, so a global canvas-mode change was avoided in that single-page revision.

## View parameters

| Parameter | Default | Meaning |
|---|---:|---|
| p_vintage_page |1| Requested six-cohort page, bounded by the filtered cohort count |
| p_vintage_mob_start |1|1 forMOB 1–6;7 forMOB 7–12 |

All common tabs, registry drill and return now retain 11 parameters, including these two. A reporting-date or segment change clamps an out-of-range page to the last valid page. Empty scope shows **No cohorts · Page 1 of 1** with no stale matrix cells. Cohort paging and age selection do not alter the underlying measures, cards or curves.

## Data and rendering

The complete `vintage_matrix` dataset remains available. New `vintage_matrix_view` selects the visible block in SQL using the same bounded cohort rank and normalized age block as `vintage_kpis`. It preserves every original cell's value and observation status. Native widgets read literal rows1–36 from this view, with ROWCOUNT guards for partial/empty results. `filter_vintage_mob` supplies the two age choices.

The initial implementation used nested dataset VALUE expressions to calculate native row indices. Preview exposed stale/blank cells under that approach; the final implementation moves only block selection into SQL. A regression check now rejects nested dynamic row addressing, and a real database test verifies that the eight visible blocks partition all288original cells exactly. The saved before/final receipts remain under `validation/vintage-readable/`.

## Verified scope

- Narrow desktop panes at **640×900** and **722×1030**, and wide **1440×900**. Values and cohort labels are readable; desktop theme and chart placement are preserved.
- All 8 blocks: all 288 visible cells match the original full matrix through actual Preview inspection.
- Repeated cohort paging, both age choices, unchanged cards/curves, and retained view state through all four other stories.
- Historical August 2025: requested page 4 clamps to page 2, with four populated cohorts and two blank rows. Empty scope clears every data cell.
- **54 tests pass**, including 11 Vintage SQL tests and 2 native artifact tests. Fresh source review and follow-up found no Critical/Important defects. No new browser console errors.

The layout is verified for desktop panes at least 640 px wide. Smaller phone screens require a separate composition. At any width, only a 6×6 block is visible at once; pagination is the deliberate tradeoff for readable values. The native vendor trial notice remains visible.

[Original wide screenshot](../validation/vintage-readable/matrix-1440.jpg) · [Narrow screenshot](screenshots/vintage-readable-narrow.jpg) · [Delivery receipt](../validation/vintage-readable/delivery.json) · [Runtime block comparisons](../validation/vintage-readable/runtime-blocks.json) · [Test log](../validation/vintage-readable/tests.txt).


## Shared scrolling layout follow-up

The November 5 update adapts the remaining pages and common controls to desktop panes from 640 px wide. All original fields, dataset scopes and actions remain available. See [narrow desktop layout](narrow-pages.md) for the current frame and verification.


The compact desktop layout has now been restored on all five stories. Vintage again places the curve and guide beside the readable matrix. See [current layout](desktop-layout.md).
