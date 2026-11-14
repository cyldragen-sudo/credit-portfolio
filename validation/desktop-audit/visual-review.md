# Desktop visual and meaning review

Reviewed 2026-11-05, read-only product inspection. No source, dataset or dashboard changes made.

## Evidence and scope

Directly inspected all five current 1440×900 JPGs in `docs/screenshots/` using the image viewer:

- `portfolio-overview.jpg`
- `sales-and-funnel.jpg`
- `delinquency-quality.jpg`
- `vintage-analysis.jpg`
- `loan-details.jpg`

Traced the shared desktop polish, page geometry, chart builder and chart-unit/label source in `dashboard/desktop_layout.py`, `dashboard/build_report.py`, all four subsidiary page modules, and the corresponding `src/` query builders. This is a visual/meaning check, not a recomputation of portfolio results.

The Vintage evidence intentionally shows cohorts 13–18, MOB 7–12; it is an exercised saved view, not a default-state screenshot. The Loan Details evidence shows the contract reached from the quality registry.

## Findings

No new P1/P2 visual defect established in the five supplied desktop captures. No clipped KPI value, intersecting table value, overlapping panel, missing chart title, missing essential unit, or obscured record row was observed.

One environment limitation is visible on every page: the FineVIS unregistered-function notice covers the lower-right footer area (roughly x571–1420, y810–870 at this capture size), including the `DEMO · NOT REGULATORY REPORTING` footer. The top-right `SYNTHETIC DATA / RUB` badge remains visible, and the notice does not cover chart or table data in these captures. This is a known vendor trial overlay, not evidence that the compact dashboard geometry is defective.

Compact table/axis/caveat text is visibly smaller than the main KPIs. It remains readable when inspected at the original desktop capture size; font-size preference alone is not treated as a defect. Readability at 1366 and 1920, different operating-system scaling, and browser zoom should be concluded from the fresh render review being performed separately.

An initial suspicion that Quality's first KPI clipped its `R` was disproved by examining the isolated original pixels: `quality-kpi-crop.jpg` shows the full `RUB 185.88 m` with left padding. Do not file a clipping defect for that card.

## Page checks

| Page | Visual/task assessment | Meaning checks |
| --- | --- | --- |
| Overview | Six KPIs, two trend panels, product chart and six-row regional table fit their panels. Date, active top tab, filters and Apply are distinct. | Portfolio/product/region units consistently use RUB bn; monthly funding uses RUB m. Delinquency subtitle identifies whole-loan principal exposure and percent of portfolio; both series are labeled. Regional growth explicitly refers to the preceding month end. |
| Sales and Funnel | All funnel stages are identified by ordered counts beneath the shape. Three charts and both summary tables fit. | Funded-date sales and submission-cohort conversion are expressly distinguished. Funnel outcomes are dated at month end. The monthly plan panel visibly says ALL CHANNELS and explains that the channel filter does not apply. Funded counts of 400 and 326 therefore are not inherently conflicting. Amount charts/table use RUB m. |
| Delinquency and Portfolio Quality | Seven-column transition matrix and eight-row registry are dense but fit; diagonal shading aids reading. Loan references are teal, and the registry heading explains the detail drill. Threshold and pagers have room. | Full-loan exposure differs visibly from unpaid scheduled principal/interest. Matrix specifies opening cohort, percentage and count, and explains diagonal/zero/missing states. Registry monetary headers use RUB and DPD is separately labeled. Threshold label explicitly requires Apply; footer says the threshold affects the list only. |
| Vintage Analysis | Six cohorts × six ages are large and legible. Cohort pagination and MOB range sit outside cell data. Curves and reading guide fit beside the matrix. | Percent of original loans, complete anniversaries, immature/unavailable dash, newest-first order and rounding are explicit. Guide explains pooled mature-cohort KPI denominators, sampled curves and cumulative ever delinquency versus current loss. Query multiplies ratios by 100, matching displayed percentage units (`src/vintage.py:33–38`). |
| Loan Details | Identity, selected date, six KPIs and contract attributes are visible. Two histories and independent eight-row record tables fit. The three-row operations example leaves unused striped rows rather than colliding with the footer. Back-to-registry action is prominent. | Principal history is RUB m, DPD history is days, and individual amounts/record headers use RUB. Issue date and contractual maturity are separate from observed close date. Footer explains that contract selection follows loan ID/As of while portfolio filters are retained for return. |

## Source support and limits

- Desktop canvas/AUTO scaling and compactness: `dashboard/desktop_layout.py:5–7`; native table type increases and guide/chart font polish: lines 26–38.
- Shared chart subtitles, series binding, legends and formatting: `dashboard/build_report.py:113–165`. Amount and percent conversion agree with the inspected subtitles in `src/overview.py:66–68`, `src/sales.py:52–67`, `src/delinquency.py:59–65`, and `src/loan_details.py:72–78`.
- Native line charts have a zero y-axis baseline in `build/default-line.xml`; the supplied column charts also visibly start at zero. No misleading truncated baseline observed.
- Navigation source carries the eleven existing parameters and guards loan opening; this is source inspection only, not a click-through verification. Shared filter controls and Apply are visually present on all pages.
- No browser interaction was performed. Dropdown contents, focus/keyboard usability, tooltip rendering, hover colors, runtime page changes, pending-versus-applied states, empty states, and other filter combinations are outside this visual evidence. Source inspection does not establish their runtime correctness.
- No claims are made about phone/narrow layouts, browser accessibility metrics, or exact WCAG contrast compliance. No broad numerical audit was conducted.

## Recommendation

Preserve the intentional compact desktop arrangement. The supplied 1440 captures do not justify a reflow or global font enlargement. Combine these notes with the fresh 1920/1366 rendering and interaction evidence before declaring the whole audit complete.
