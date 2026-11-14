# Compact desktop layout restored

The current report uses the established **1920×1080 desktop canvas with AUTO fitting**. All five pages fit one dashboard canvas: six KPI cards in one row, related charts side by side, and records in tables. The earlier 6600-pixel scrolling composition has been removed at the user's request.

The English interface, navy/teal/amber palette, five stories, 31 datasets, ten charts and eleven retained parameters are preserved. Source data, SQL, metric definitions and connection permissions are unchanged.

## Readability fixes retained

- Vintage retains the large **six cohorts × six MOB ages** matrix, cohort pagination and two MOB ranges; its curve and guide are beside the matrix.
- Apply uses the native fontStyle setting, so its label has the intended desktop size.
- Explanatory text wraps within widget bounds; KPI notes have room for two lines.
- Navigation, chart axes and dense table values use modest desktop font increases.
- Panels and row stripes paint behind labels and values.

The compact quality matrix shows percentage and loan count on one line with a slightly larger font. The registry retains eight tabular records per page. Operations and payment schedule retain eight rows and independent pagers. This layout does not promise phone-sized readability; opening a normal desktop-width browser window gives the intended density.

## Navigation and filters

Choose the month, product, region and channel, then press **Apply**. The five top tabs carry all eleven parameters, including registry threshold/page, selected loan, both detail pages and Vintage page/MOB range. A teal loan reference opens Loan Details and resets its two record pages. **Back to registry** restores the saved portfolio slice and list state.

As before, explicit numeric parameter URLs can restore a slice after a full reload. Transient control selections are not automatically saved into bookmark URLs. Unsupported diagnostic dictionary IDs initially produce an empty scope and normalize to an available control value on Apply.

## Evidence and rebuild

Current screenshots and checks are under `validation/desktop-restored/`. Native tests require the compact canvas, six cards in a row, side-by-side charts, tabular records, readable notes and native Apply font. Existing tests continue to verify all twenty navigation bindings, guarded loan drills, independent pagers and literal Vintage dataset rows. A source-preservation comparison verifies unchanged datasets, parameters and actions.

Layout-only rebuild:

```bash
python3 dashboard/build_report.py --local
python3 dashboard/build_report.py
python3 dashboard/install_report.py --replace
```

The installer privately backs up the previous report. `dashboard/desktop_layout.py` owns presentation polish; the original page modules own desktop geometry. The previous scrolling layout and its screenshots remain historical evidence in the earlier archive and `validation/narrow-pages/`. The vendor trial notice remains visible.


Final verification: all five pages passed desktop checks at 1440×900 and 1920×1080, without content scrolling or detected text overflow. All 23 recorded runtime checks passed, including combined historical filters, registry drill/return and retained table/Vintage view state. The full PostgreSQL-backed suite passed all 55 tests without skips.


## Desktop audit follow-up

The subsequent desktop audit found the native trial notice overlapping the last registry/payment rows at 1920×1080 and 1366×768. Vertical spacing is now tightened by 10% while keeping the desktop grid, every font, text/control height and all data/navigation bindings unchanged. Panels and chart heights follow the tighter spacing. A reserved bottom strip keeps the native notice clear of the data; the vendor notice remains visible. See [desktop audit](desktop-audit.md) for before/after evidence and the final scope.
