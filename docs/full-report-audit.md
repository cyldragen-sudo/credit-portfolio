# Full five-page report verification

**Follow-up:** the narrow Vintage finding below was subsequently resolved for desktop panes from 640 px wide with a paged 6×6 matrix. See [readability verification](vintage-readable.md). This document and its scorecards retain the earlier audited revision.

**Assessment: Share with caveats. Completeness: Complete within the reviewed scope.**

Verified November 4, 2026. All five pages are usable on a wide desktop display. No P 0/P 1 numerical or navigation defect was found. The report template, SQL, fixture and permissions remain unchanged; this review adds evidence and documentation. One P 2 readability limitation remains for the dense Vintage matrix on a narrow viewport.

[Open Portfolio Overview](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=1).

## Scope and method

The inventory contains 30 KPI cards, ten native charts, eight tables/matrices and one contract-attribute panel. All installed dataset SQL was compared with current source. Independent computations use original loan/operation/application/schedule/allocation records rather than treating a dashboard helper as proof.

The numerical audit covers default October 31, 2026; historical August 31, 2025 with Personal Loan / Moscow / Online; empty region 999 and missing contract; plus early reporting, dated closure/write-off and DPD boundary samples. Browser verification covers all five pages in default, filtered historical and empty states. Additional all-channel historical cases verify date changes through Apply. These are named representative scenarios, not an exhaustive rendering of every date, segment combination or contract.

Twenty distinct directed tab transitions were observed in authenticated Preview. The shared four filters, registry threshold/page, selected contract and both detail pages are retained. All five Apply buttons were exercised after sign-in. Registry threshold 91+ changed only the list; registry and detail pagers were repeatedly exercised. A registry click opened loan 8259, reset both detail tables to page 1, and returned to threshold 91+/registry page 2. The known historical selected loan 954 retained both detail pages at page 2 across navigation.

Desktop review used 1440×900. A narrow viewport sample specifically examined the dense Vintage matrix. Charts were inspected after native animation settled. Currency, percentage and day units match the supplied metric contract. The report uses synthetic data through October 31,2026; it does not assert current real-bank performance.

## Dashboard best practices and quality

| Category | Observed defects | Assessment |
|---|---|---|
| Dashboard usefulness and completeness | 0 / 5 | All five requested analytical jobs and their major sections are present and usable in the checked desktop scenarios. |
| Analytical clarity | 0 / 5 | Five page purposes and nearby definitions are coherent: funded flow versus submission cohort, all-channel plans, full-loan exposure, cohort maturity and contract-specific scope remain explicit. |
| Visual and interaction consistency | 1 / 40 | All five desktop pages, twenty directions, filters, Apply and pagers passed. One sampled narrow view makes the dense Vintage matrix too small to read; desktop viewing is the supported practical use. |

## Analytical correctness and robustness

| Category | Observed defects | Assessment |
|---|---|---|
| Source authority and confidence | 0 / 49 | All 49 numeric components trace to the declared synthetic fixture, source definitions and matching installed SQL. No real-bank claims are made. |
| SQL/value accuracy | 0 / 49 | All 30 headline KPIs, ten charts, eight tables/matrices and the contract attribute panel reconcile to independently reconstructed inputs. Browser cases cover default, filtered historical and empty scopes; this is not every possible filter combination. |
| Within-chart agreement | 0 / 10 | Ten charts were inspected on desktop; source values, percent/RUB units, legends and final rendered marks agree. Animation intermediates were excluded from final assessment. |
| Complete source details | N/A | No interactive source-detail surface is part of this native FineVIS report; SQL/lineage is verified through the delivered project. |
| Cross-artifact consistency | 0 / 10 | Ten named component relationships reconcile, including stock/flow, exposure/buckets, cohort denominators and contract ledgers. |
| Data-quality controls | 0 / 49 | Eligibility, dated outcomes/allocations, closed/write-off states, zero versus NULL and cohort maturity were checked. Edge dates and contracts are sampled rather than exhaustive. |
| Conclusion support | N/A | The dashboard makes descriptive measurements and definitions, without causal or prescriptive business conclusions. |

Counts are scoped inventory units with observed remaining defects, not accuracy percentages or proof that every possible state was rendered. Categories overlap and must not be summed. N/A source-detail means the report has no separate interactive source panel; its delivered SQL and definitions were still checked.

## Prioritized problems and proposed fixes

1. **P 2 — Vintage Analysis, narrow viewport:** the fixed native canvas scales a 24-cohort matrix too small to read comfortably. **Fix (Proposed):** view it on a wide desktop screen; a separate responsive/mobile composition can be designed later. No layout redesign was applied in this review.
2. **Operational incident — expired FineReport session:** during the review, Apply left old values visible and a fresh navigation redirected to login. **Resolved:** the user signed in again; the same four-filter change, including after revisiting Overview, and all five Apply buttons then worked with no new console errors. No report-configuration defect was demonstrated, and no authentication or license setting was changed.

The vendor FineVIS trial notice remains visible. Native navigation preserves transient session selections; an explicit numeric-parameter URL is still required to restore an exact slice after a full reload. Loan Details follows loanID/date, while product/region/channel retain portfolio-return context. Sales plans intentionally use all channels; submission cohorts and funded-date sales are different populations. Vintage rates retain original denominators and only fully mature cohorts.

## Evidence

- [Component inventory](../validation/full-audit/inventory.json), [native bindings](../validation/full-audit/ui-bindings.json), [coverage record](../validation/full-audit/coverage.json) and [coverage summary](../validation/full-audit/coverage-summary.json).
- [Independent Overview/Sales results](../validation/full-audit/overview-sales.json) and [reusable calculation](../validation/full-audit/overview-sales.py):123 checks passed.
- [Independent Quality/Vintage/Details results](../validation/full-audit/quality-vintage-details.json) and [reusable calculation](../validation/full-audit/quality-vintage-details.py):10,471 checks passed, including independent obligation reconstruction and anniversary eligibility.
- [Installed dataset results](../validation/full-audit/native-results.json), [capturing script](../validation/full-audit/native-sources.py), [KPI display cases](../validation/full-audit/runtime-cards.json) and [all 20 navigation observations](../validation/full-audit/navigation.json).
- [Interaction receipt](../validation/full-audit/interaction-checks.json), [post-sign-in console](../validation/full-audit/post-auth-console.json), [permissions/archive integrity](../validation/full-audit/integrity.json) and [current 49-test suite](../validation/full-audit/tests.txt).
- Desktop page evidence is stored as `validation/full-audit/page-{1..5}-{default,filtered,empty}.jpg` and matching text. [Narrow matrix sample](../validation/full-audit/vintage-narrow.jpg).

The helper scorecard was generated from the actual component record using its unchanged library exports; the desktop environment has no command-line Node executable, so the helper's CLI adapter was omitted for library execution. No product behavior depends on that tooling.
