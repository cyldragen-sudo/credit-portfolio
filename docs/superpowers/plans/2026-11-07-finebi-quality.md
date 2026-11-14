# FineBI Portfolio Quality Implementation Plan

> Execution: continue the authorized native FineBI migration in this session.

**Goal:** Add Delinquency and Portfolio Quality to the existing native shared Tab dashboard.
**Architecture:** Reuse four prepared quality SQL datasets, the existing synthetic PostgreSQL source and shared filter controls. Add six KPI cards, DPD bucket exposure, a seven-state transition matrix and a native loan registry. A local English DPD threshold controls only the registry.
**Tech Stack:** FineBI 6 native SQL datasets, charts, cross table, detailed table, Tab and dropdown controls.
**Spec:** ../2026-11-07-finebi-migration.md and ../../delinquency-quality.md.

## Constraints and checks

Preserve Overview and Sales, English labels, teal/navy theme and desktop tables. Keep overdue scheduled amounts distinct from whole-loan exposures. Matrix rows retain their opening denominators, including terminal states; zero denominator is a dash. All four shared filters persist across three tabs. Native registry scrolling/paging may replace FineReport's eight-row paging. No Details drill target exists yet, so it belongs to the authorized later Loan Details page.

- [x] Install four label-aware SQL datasets through native UI; verify defaults and Text parameters. Include readable registry threshold mapping with numeric fallback.
- [x] Create six quality KPI cards, ordered DPD exposure chart, native transition cross table and complete registry; preserve source calculations and rates.
- [x] Place components in a third native Tab, add local registry threshold and brief metric/matrix notes; bind global parameters to all quality sources.
- [x] Verify defaults, historical segment, threshold isolation, matrix denominators, registry access and all navigation paths involving the new tab. Restore defaults, release editor, save screenshots and completion metadata.

## Final evidence

Nine native components plus registry threshold and method note saved in the
existing report. Used native Color Table instead of numeric-only pivot to
preserve cell text containing share and exact count with zero-denominator
dashes. The matrix uses black 12px text; all seven states fit. All nine registry
columns fit; native 100-row pagination and SQL ordering verified.

All default and historical KPIs matched source. 91+ threshold returned 473
rows with summary metrics unchanged; native page two anchor matched source
row 101. A valid November 2024 Mortgage / Novosibirsk / Partner / 91+ scope
showed zero rows. Every directed path among the three tabs retained the
historical shared controls and registry threshold. Defaults restored.

89 English/numeric parity checks passed. Independent read-only review found
no material findings. Final saved view checked outside editor; native Back
released editing, temporary viewport reset. State and source IDs are in
finebi/quality-build-state.json; screenshots are in outputs/finebi-quality
at the workspace root. Vintage and Details remain later migration scope.
