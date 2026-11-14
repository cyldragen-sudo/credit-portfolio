# Loan Details

[Open an example contract](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=5&p_loan_id=2170).

In **Portfolio Quality**, click a teal loan reference in the registry. The fifth native FineVIS story opens that row's contract at the applied month end. **Back to registry** restores the portfolio view with its applied month/product/region/channel, delinquency threshold and registry page. All records are synthetic.

## What the page shows

| View | Meaning |
|---|---|
| Principal balance | Outstanding principal at the selected end-of-day date, including overdue principal |
| Overdue principal / interest | Unpaid scheduled amounts past their due dates |
| Days past due / contract status | The selected date's snapshot state |
| Cash received | Cumulative repayment and prepayment principal plus interest through the selected date; disbursements and write-offs are excluded |
| Contract attributes | Original principal, annual percent rate, original term, issue date, contractual maturity and observed close date |
| Origination context | Region, branch, channel and original risk band |
| Principal / delinquency history | Calendar month-end snapshots from November 2024 through the selected date; balance chart uses RUB millions, DPD chart uses days |
| Operations | All dated contract operations through the selected date, newest first, with separate principal, interest and received cash |
| Payment schedule | All installments from a schedule already effective at the selected date, ordered by installment number; due principal, due interest, paid allocation, write-off allocation and observed status |

Amount cards and tables retain full RUB values with two decimal places. Annual rate is already stored in percent units. Future schedule installments may be displayed because they are part of the contract already known at the selected date; their future payment outcomes are excluded.

Both tables show eight rows per page with independent Previous/Next buttons. Operations sort by date descending then operation ID descending; the fixture's single-version schedule sorts by installment number. Page requests are bounded and clamp after date or contract changes. Clicking another registry contract resets both detail tables to page 1. No operation or installment is silently dropped by a display limit.

Schedule **Paid** combines principal and interest cash allocations; **Written off** combines principal and interest debt-extinguishment allocations. These are distinct from original amounts due. **Cancelled** means cancellation had occurred by the selected date; future cancellation dates are hidden. Otherwise installments are Settled, Overdue, Due today or Scheduled based on dated allocations and the selected date. The graph is not a daily event chart; use the dated operations and schedule for exact event lookup.

## Scope and parameters

Details follow **loan ID and As of**. Product, region and channel remain portfolio return context and do not hide the chosen contract. The page footer explains this distinction. Changing As of and pressing Apply recalculates the contract, cash, allocations and history; it cannot expose future close or cancellation information.

| Parameter | Default | Purpose |
|---|---:|---|
| p_loan_id | 0 | Contract selected by a registry row; zero displays an explicit selection prompt |
| p_operation_page | 1 | Requested operations page |
| p_schedule_page | 1 | Requested payment schedule page |

All navigation retains these three parameters plus the Vintage view parameters `p_vintage_page` and `p_vintage_mob_start`, and the existing `p_date_key`, `p_product_id`, `p_region_id`, `p_channel_id`, `p_min_dpd` and `p_quality_page`. Registry references pass the actual row's loan ID and reset both detail page parameters. Empty registry rows are guarded and cannot open a contract. Unknown or not-yet-issued IDs produce empty details and dash cards.

Native navigation updates only `page_number` in the URL; transient selections remain in the report session. Bookmark an explicit numeric parameter URL, including `p_loan_id` and date, to restore an exact contract view after reload. Opening Loan Details from its tab retains the last selected contract; without a prior selection, it shows the selection prompt.

## Data lineage and validation

`src/loan_details.py` adapts supplied queries 11–14 into five native projections: `loan_kpis`, `loan_operations`, `loan_schedule`, `loan_balance_chart` and `loan_dpd_chart`. A dated selected snapshot gates every detail dataset. Headers mask future closure, operations and allocations stop at as-of, and schedules require an effective contract. The underlying fixture, schema and reporting permissions are unchanged.

Eight real PostgreSQL tests independently reconcile snapshots and cash, historical masks, schedule allocations, chronology, terminal states, missing/unissued IDs and stable bounded pagination. Native tests require five stories, 31 datasets, ten charts, twenty common navigation bindings with eleven parameters, eight guarded row-ID actions and four independent table pager actions. A fresh reviewer reran the eight database tests and native test and found no Critical/Important defects.

Authenticated Preview opened registry loans 2170, 9183 and 954; verified a return to August 2025 / Personal Loan / Moscow / Online, registry page 2 of 3; repeatedly paged both tables; preserved the selected contract and operations page across the eight directions linking Loan Details to the other four stories; reset pages on a new registry selection; and inspected historical, closed, written-off, unknown and oversized-page states. A broader rapid-navigation audit encountered browser-control timeouts, so runtime evidence claims the eight new directions rather than all twenty. All twenty bindings pass structural tests. Final browser console inspection recorded no errors.

See `validation/loan-details-tests.log`, `validation/loan-details-delivery.json`, `validation/preview-loan-*` and `docs/screenshots/loan-details.jpg`. The portable report uses the named CREDIT_PORTFOLIO connection and includes no credentials; the installed report uses the protected local SELECT-only connection. FineVIS's vendor trial notice remains visible.


## Shared scrolling layout follow-up

The November 5 update adapts the remaining pages and common controls to desktop panes from 640 px wide. All original fields, dataset scopes and actions remain available. See [narrow desktop layout](narrow-pages.md) for the current frame and verification.


## Current desktop layout

The compact desktop composition has been restored. Charts sit side by side, KPI cards occupy one row, and records remain tabular. Readability fixes, filters, paging and navigation are preserved; see [desktop layout](desktop-layout.md). Earlier scrolling-layout notes describe a superseded revision.
