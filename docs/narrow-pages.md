# Historical scrolling-layout experiment

**Superseded:** the user requested restoring the compact desktop report. The current implementation is described in [desktop layout](desktop-layout.md). Everything below records the earlier scrolling revision and its validation.

The installed native FineReport report now uses width fitting and vertical scrolling on all five stories. The target is a desktop browser pane **640 px or wider**. This is a shared scrolling layout at every width, including wide windows; it is not a separate mobile report or a breakpoint-dependent compact desktop layout.

## What changed

- Common navigation, dropdowns and Apply are larger. The four portfolio filters occupy two rows.
- Six KPI cards use three columns and two rows. Long explanatory text wraps within its card.
- Charts occupy the page width and use larger native axis/legend fonts.
- Overview shows each of the six regions as a labeled record, retaining all six measures.
- Sales preserves the funnel, both other charts, product plans and channel conversion. Plan figures still use all channels, as the visible scope note explains.
- Portfolio Quality retains the full seven-state transition matrix. Each transition's percentage and loan count occupy separate lines. The registry retains eight loans per page, with nine fields arranged over three lines per loan.
- Loan Details retains contract attributes, both history charts and eight rows per operation/schedule page. Schedule fields use two lines per installment. Both table pagers remain independent.
- Vintage keeps the same six cohorts by six ages, all cohort pages and both MOB ranges. Its sections and shared controls follow the common scrolling frame because FineVIS canvas adaptation is report-wide.

The report still contains **five stories, 31 live datasets, ten native charts and eleven retained parameters**. No SQL, fixture, metric definition or connection permissions changed. Native widget IDs and original navigation/drill/paging actions remain intact. New record labels are native text widgets. Transition display line breaks use native formulas; their percentages/counts keep the original data.

## Use

Open [Portfolio Overview](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=1), choose filters and press **Apply**. Scroll down to the remaining sections. The five tabs remain at the top of each page; scroll back up to change pages.

Select a teal loan reference in Portfolio Quality to open its details. **Back to registry** restores the applied slice, threshold and requested list page. Use the independent Previous/Next controls for operations and schedule records. Vintage page/MOB state also survives navigation through the other stories.

As before, explicit parameter URLs restore a slice after a full reload; temporary control selections are not written into bookmark URLs. Loan Details follows the selected loan and date while retaining portfolio filters for return.

## Verification

Evidence is in `validation/narrow-pages/`: screenshots at 640×900, 722×1030 and 1440×900; runtime interaction receipt; native structure tests; complete PostgreSQL-backed suite; and final delivery hashes. All four requested pages were inspected at the three widths, including lower record sections. Width checks compare actual native widget edges against the viewport's usable width, accounting for the vertical scrollbar.

Runtime checks exercise historical August 2025 / Personal Loan / Moscow / Online, Apply, 91+ registry filtering, loan drill/return, independent detail pagination, retained Vintage page/MOB state and empty results. Previous independent metric reconciliations remain valid because the source queries are unchanged. A fresh read-only review confirmed every original widget ID, action, filter binding and displayed record field survives the layout pass.

FineReport's existing vendor trial notice remains visible and can cover part of the bottom of a viewport. It does not change calculations or access to sections by scrolling. Phone widths below 640 px are outside this desktop layout's verified scope. For deliberately unknown numeric filter IDs in diagnostic URLs, the dataset initially returns an empty scope; Apply normalizes the dropdown to an available dictionary selection. Normal user selections use the listed filter values.

## Rebuild

`dashboard/readable_layout.py` owns the native layout pass invoked by `dashboard/build_report.py`. For layout-only changes, reuse the existing serialized datasets:

```bash
python3 dashboard/build_report.py --local
python3 dashboard/build_report.py
python3 dashboard/install_report.py --replace
```

The installer backs up the previous owned report privately. Portable delivery remains `dashboard/report/Portfolio_Overview.fvs` with the named `CREDIT_PORTFOLIO` connection and no local credentials.


[Overview at 722 px](screenshots/portfolio-overview.jpg) · [Sales at 722 px](screenshots/sales-and-funnel.jpg) · [Quality at 722 px](screenshots/delinquency-quality.jpg) · [Loan Details at 722 px](screenshots/loan-details.jpg). All 34 recorded runtime checks passed after completing the final authenticated repetition.
