# Validation record

The original fixture was validated on November 4, 2026 against **PostgreSQL 16.2**, using a temporary isolated local cluster that was stopped afterwards. The database is now also deployed in a separate persistent project cluster on 127.0.0.1:55433. No existing ATM/DC project database was changed.

## Five-page report deployment

The complete project suite contains **56 passing tests**, including five overview SQL tests, six sales SQL tests, eight quality SQL tests, eleven vintage SQL tests, eight Loan Details SQL tests, native report binding/navigation checks and the private-file exclusion test. The installed report was opened in the running FineReport/FineVIS Preview and visually inspected. It contains five stories, 784 native widgets, thirty-one datasets and ten native charts. All four filters, combined product/region/channel scope, historical August 2025 and an empty region selection were exercised. The prior four-page audit exercised all twelve directions. The current audit observed the eight directions connecting Loan Details and retained the selected contract, shared filters, registry threshold/page and detail page state. All twenty common navigation bindings are tested structurally. Overview's original RUB 19.55 bn balance remains unchanged. Vendor trial notices remain visible.

Quality's default totals reconcile to independent snapshot/ledger sums: overdue principal RUB 185,878,893.27, overdue interest RUB 168,526,708.29, 1,268 past-due loans and monthly principal write-offs RUB 25,499,741.53. The seven-state matrix reconciles to the complete 11,600-contract opening cohort. Final authenticated Preview confirmed repeated paging 1 → 2 → 1 → 2, 91+ registry-only filtering, historical combined scope, empty results, oversized-page clamping and all navigation paths, with no new console errors. See [quality validation](delinquency-quality.md#validation).

Sales checks independently reconcile funded-date volumes to disbursement operations and historical cohort counts to dated application events. They verify that the monthly plan does not change with channel selection, that scoped sums match direct joins, that empty scopes return dash ratios and empty charts/tables, and that trends stop at the selected cutoff. Native report tests require the actual VanChartFunnelPlot, five stories and explicit eleven-parameter navigation actions.

See `validation/loan-details-tests.log`, `validation/loan-details-delivery.json`, `validation/vintage-tests.log`, `validation/vintage-delivery.json`, `validation/quality-tests.log`, `validation/quality-delivery.json`, `validation/native-datasets.json`, `validation/local-database.json`, `validation/report-installation.json` and the screenshots under `docs/screenshots/`. Runtime evidence is recorded under `validation/preview-loan-*`, `preview-vintage-*`, `preview-quality-*`, `preview-sales-*.txt` and `preview-navigation-overview.txt`. The portable report uses CREDIT_PORTFOLIO; the installed local report uses a protected SELECT-only report-specific JDBC connection.

Vintage adds original denominators and strict whole-cohort anniversary maturity. Its default 24-cohort window contains 8,759 original contracts; fixed-age rates at MOB 3/6/12 use 7,525 / 6,308 / 3,956 original contracts respectively. Authenticated Preview verified all twelve navigation paths, retained quality registry state, historical and empty scopes, initial-month immaturity and explicit-URL reload. A fresh reviewer independently reconciled 120 historical filtered cells against daily DPD snapshots, including 45 observed cells; no Critical/Important source defects were found. See [vintage validation](vintage-analysis.md#validation).

Loan Details independently reconciles selected-date snapshots, actual cash and effective schedule allocations. Preview opened three actual registry IDs, returned to a historical filtered registry page 2, repeatedly paged both detail tables, observed historical closure masking, closed/written-off states and missing IDs, and clamped oversized table page requests. A fresh reviewer reran its eight PostgreSQL tests and the native report test and found no Critical/Important defects. See [detail validation](loan-details.md#data-lineage-and-validation).

## Original fixture results

- **13 automated tests passed**, including real PostgreSQL report regressions. Without PGDATABASE, two database-dependent tests are explicitly skipped; the recorded run includes them.
- **15 database reconciliation checks passed**, with zero inconsistent records. Exact machine-readable results are in `validation/database-checks.json`.
- **15 FineReport dataset queries executed in three scopes**: default reporting date, historical mid-month cutoff and empty/unknown selection, for 45 successful query executions.
- Every one of **5,405,234 daily principal balances** reconciled to disbursements minus repayments, prepayments and write-offs.
- All **783,336 installment principal amounts** reconcile to original funded principal by loan. Operation principal and interest components reconcile to **395,315 allocations**, without schedule-component overallocation.
- Final-date DPD and overdue amounts reconcile to unpaid obligations. Historical DPD/overdue checks also cover December 31, 2024, August 15, 2025 and June 30, 2026.
- Every monthly-age ever-31+ flag was independently compared to dated obligations still unpaid at the end of due date + 31, reconstructed from allocation events.
- Snapshot histories are complete, ever flags are monotonic, monthly transitions retain the opening cohort, and anniversary dates are correct.
- The loader rejects an occupied schema without changing its 12,000 contracts. A deliberately invalid SQL load using a small fixture rolled back both schema and data. See `validation/loader-checks.json`.
- A SELECT-only reporting role successfully read the overview and was refused an UPDATE. See `validation/access-checks.json`.

## Independent review

A fresh reviewer found one historical schedule eligibility issue: an unissued loan's future schedule could appear before origination. A failing real-database regression reproduced it, query 13 was corrected to require an effective schedule by the as-of date, and the full suite passed. The follow-up review found no remaining Critical/Important issues in that fix and the additional historical/vintage checks.

## Scope limits

All five pages are built and rendered. Loan Details uses monthly history charts and independent eight-row table pages. A rapid broad-navigation audit encountered browser automation timeouts; its final runtime receipt claims the eight new directions rather than all twenty. All twenty source bindings pass the native test. Historical DPD reconciliation samples three additional dates rather than replaying every obligation for every day. Generic historical/empty query execution checks prove successful execution; selected regression tests additionally assert unissued-loan exclusion and original vintage denominators. These checks validate the generated demonstration, not the economic realism or predictive calibration of its scenario probabilities.

## Reproduce

After loading the supplied fixture into an empty PostgreSQL database and setting PGHOST/PGPORT/PGDATABASE/PGUSER/PSQL:

```bash
python3 -m unittest discover -s tests -v
python3 src/verify.py
```

`src/verify.py` refreshes the recorded reconciliation results, catalog dictionary and CSV page samples. Run it against a database initialized from this package's delivered manifest.


## Full five-page audit

A subsequent complete audit verified all twenty directed tab transitions in Preview, all nine retained parameters, all five Apply buttons, repeated registry/detail pagination and selected-row drill/return. Independent raw-data calculations found no P 0/P 1 discrepancy across the named default, historical, empty and boundary scenarios. Current tests:49 passed. No report, SQL or fixture change was required. One P 2 caveat remains for narrow Vintage matrix readability. An expired session interrupted refresh; authenticated repetition passed on all five pages. See [full review](full-report-audit.md) for the two scorecards, scope limits and evidence.


## Vintage readability follow-up

The earlier narrow matrix finding is resolved for desktop panes from 640 px wide. The native matrix displays 6×6 large cells with cohort paging and a two-block MOB selector. All 288 cells were checked through all 8 blocks in Preview, and retained view state, historical clamping, empty clearing and 1440/722/640 px rendering passed.54 tests passed. The complete matrix and metric definitions are unchanged. See [readability verification](vintage-readable.md). Historical full-audit receipts retain the revision they originally assessed.


## Narrow desktop follow-up — November 5, 2026

The four remaining pages and shared five-story frame now use width fitting with vertical scrolling. Larger controls, wrapped notes, full-width charts and labeled records preserve all fields and native actions. The complete 55-test PostgreSQL-backed suite passes without skips. Runtime checks and screenshots cover 640, 722 and 1440 px, historical filters, Apply, registry threshold/paging, loan drill/return, independent detail paging, retained Vintage state and empty selections. See [narrow layout](narrow-pages.md) and `validation/narrow-pages/`. Earlier audit sections describe their historical revisions.


## Desktop restoration — November 5, 2026

The user requested restoring the compact desktop composition. All five stories again use 1920×1080 AUTO fitting, six KPI cards per row, side-by-side charts and tabular records. The six-by-six Vintage matrix, wrapped notes, native Apply font, improved desktop typography and background ordering remain. The complete 55-test PostgreSQL-backed suite passes. Current screenshots, runtime checks and source-preservation evidence are in `validation/desktop-restored/`; see [current desktop layout](desktop-layout.md). The earlier scrolling revision is historical.


## Desktop UI audit — November 5, 2026

All five pages were audited at1366×768 and1920×1080. All20 directed routes retain filters/context, all5 Apply buttons refresh their data,8 pager directions change actual rows independently, and a sampled registry drill/return passes. One P1 vendor-notice overlap was fixed by tighter vertical spacing while preserving fonts, desktop grid and all source/state semantics. Final text-bounds and notice intersections are clear on all ten page/viewport cases. Full suite:56 passed, no skips. See [current audit](desktop-audit.md) for scorecards, before/after evidence and exact limits. Earlier delivery records retain their original revisions.
