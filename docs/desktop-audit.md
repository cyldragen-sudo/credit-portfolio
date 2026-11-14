# Desktop report audit — November 5, 2026

**Share with caveats · Complete within the requested UI scope.** All five desktop pages, all twenty directed page transitions, five Apply buttons, eight independent pager actions and a sampled registry drill/return passed. One demonstrated P1 display problem was repaired and rechecked. The report remains a compact desktop dashboard.

The scope is table/chart readability, navigation and retained filters. Review used 1366×768 and 1920×1080, the default October 2026 slice, and a combined historical Personal Loan / Moscow / Online slice. Current SQL results were used to check thirty refreshed headline labels across August/September 2025; this is a binding/refresh consistency check, not a new independent financial reconciliation. Prior numerical audits are retained.

The totals below are scoped inventory counts, not claims that every filter combination, loan, tooltip or browser state was verified. A zero means no observed remaining defect in that category. The record maps each scoped item to its inspected evidence.

## Dashboard best practices and quality

| Category | Observed defects | Assessment |
|---|---|---|
| Dashboard usefulness and completeness | 0 / 5 | All five requested analytical jobs and their existing major sections remain available in the desktop composition; no requested view was removed. |
| Analytical clarity | 0 / 5 | All five page purposes and material definitions remain clear, including sales cohorts versus funded flow, all-channel plans, whole-loan exposure and cohort maturity. |
| Visual and interaction consistency | 4 / 40 | All35 control paths passed and notice overlap was repaired. Four page units retain a P2 small-table-text caveat at1366x768 (approximately9–11px); FullHD is more comfortable. No clipping or notice/data overlap remains in ten final renders. |

## Analytical correctness and robustness

| Category | Observed defects | Assessment |
|---|---|---|
| Source authority and confidence | 0 / 49 | The 49 numerical components retain the declared synthetic source, valid native bindings and unchanged SQL; portable/private/installed parity verified. |
| SQL/value accuracy | N/A | Not applicable: This request is a desktop readability/navigation audit, not a new independent raw-ledger reconciliation. All30 refreshed headline labels matched current native SQL in dated UI tests; prior numerical audits are retained. |
| Within-chart agreement | 0 / 10 | All ten charts retain coherent titles, axes, units, legends and native series bindings. Final desktop renders checked; individual marks were not independently recomputed. |
| Complete source details | N/A | Not applicable: This native FineVIS report has no interactive SQL/source-inspector surface. Delivered SQL and bindings were inspected separately. |
| Cross-artifact consistency | 0 / 20 | All twenty directed tab transitions retained shared filters and visible local context; source review verifies explicit forwarding of all eleven parameters. |
| Data-quality controls | N/A | Not applicable: Underlying fixture completeness/duplicates/freshness were not reprofiled in this UI audit. Source data and SQL were unchanged; the PostgreSQL regression suite passed. |
| Conclusion support | N/A | Not applicable: The report presents descriptive measurements, with no causal or prescriptive business conclusions to validate. |

## Prioritized problems and proposed fixes

1. **P1 — Last rows of Portfolio Quality and Loan Details overlapped by the native trial notice.** At Full HD the notice covered part of the last registry/payment row; at1366×768 it covered payment rows6–8. **Fixed:** vertical spacing was tightened by10%, preserving the desktop grid, all fonts, native text/control heights, data, formulas, actions and eleven parameters. A lower reserved strip now keeps the notice clear of data. All five pages passed final text-bounds and notice-intersection checks at both viewports, and a second reviewer inspected the rendered result. The notice remains visible. [Before](../validation/desktop-audit/loan-1366-before.jpg) · [After](../validation/desktop-audit/loan-default-1366-after.jpg).
2. **P2 usability caveat — Small dense-table text at1366×768.** Registry and schedule values render at roughly9–11px; no clipping or actual glyph collisions were observed after repair. **Fix (Proposed):** use Full HD for prolonged table inspection; keep any future table-specific enlargement within the compact desktop design. No global font enlargement or mobile-style reflow was applied.

## Verified behavior

- All twenty directed tabs preserve the four shared dropdown selections and the target's visible local state. Source review confirms explicit forwarding of all eleven parameters. The rich control slice used registry page2 / All active, loan954, both detail pages2, and Vintage page2 / MOB7–12.
- Apply was exercised on all five pages by changing reporting month. All thirty visible headline labels matched the selected native dataset results.
- Registry, Vintage, operations and schedule pagers were exercised in both directions with actual first-row changes. Detail pagers did not change one another. One actual registry reference opened the matching contract, reset both detail tables to page1 and returned to the saved list page.
- Ten charts and all existing tables/matrices remain present with titles, units, axes and relevant legends. Sales cohort versus funded-date populations, all-channel plans, whole-loan exposure and Vintage maturity/denominators remain explicit.
- All ten final page/viewport cases showed no detected text-bound violations or notice/text intersections. No new browser console errors were recorded. The original default slice was restored, the viewport override reset, and Overview left open.

## Evidence and limits

Before/after images use different dated synthetic selections; compare row visibility and geometry, not their amounts. Data/formula preservation is established by the source comparison, and retained filter behavior by the separate runtime records.

[Runtime summary](../validation/desktop-audit/runtime-summary.json) · [All20 routes after repair](../validation/desktop-audit/routes-after-fix.json) · [Five Apply checks](../validation/desktop-audit/apply.json) · [Pagers](../validation/desktop-audit/pagers.json) · [Drill/return](../validation/desktop-audit/drill-return.json) · [Final visuals](../validation/desktop-audit/visual-summary.json) · [Source/state review](../validation/desktop-audit/state-review-after.json) · [Coverage record](../validation/desktop-audit/coverage.json) · [PostgreSQL-backed regression log](../validation/desktop-audit/tests.txt).

The complete regression suite passed56 tests, including the new notice-clearance regression. Source review and baseline comparison confirm the repair changed vertical geometry only; SQL, formulas, data, fonts, chart assets and interaction bindings remain intact. Portable/private/installed parity was checked without emitting credentials.

Not covered: every loan/filter combination, keyboard-only navigation, all tooltips, formal accessibility/contrast certification, phones, exports, or a fresh independent replay of every numerical metric. Earlier1440 captures are historical observations and do not override the fresh notice-overlap evidence at the audited resolutions.
