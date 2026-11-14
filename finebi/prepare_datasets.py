#!/usr/bin/env python3
"""Package validated source SQL for manual native FineBI dataset creation."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'finebi' / 'datasets'
PARAMETERS = {
    'p_date_key': {'type': 'Number', 'default': 20261031, 'label': 'As Of Month'},
    'p_product_id': {'type': 'Number', 'default': 0, 'label': 'Product'},
    'p_region_id': {'type': 'Number', 'default': 0, 'label': 'Region'},
    'p_channel_id': {'type': 'Number', 'default': 0, 'label': 'Channel'},
    'p_min_dpd': {'type': 'Number', 'default': 1, 'label': 'Minimum DPD'},
    'p_loan_id': {'type': 'Number', 'default': 0, 'label': 'Loan ID'},
}
CATALOG = [
    ('Shared Filters', 'filter_date', 'Filter - As Of Month', 'Reporting month dropdown; id is YYYYMMDD, label is English month and year.'),
    ('Shared Filters', 'filter_product', 'Filter - Product', 'Product dropdown; id 0 means All Products.'),
    ('Shared Filters', 'filter_region', 'Filter - Region', 'Region dropdown; id 0 means All Regions.'),
    ('Shared Filters', 'filter_channel', 'Filter - Channel', 'Channel dropdown; id 0 means All Channels.'),
    ('Shared Filters', 'filter_min_dpd', 'Filter - Minimum DPD', 'Registry threshold dropdown: 0, 1, 31, 91.'),
    ('Portfolio Overview', 'overview_kpis', 'Overview KPIs', 'One row: principal balance, MTD disbursements, borrowers, monthly growth and DPD exposure ratios.'),
    ('Portfolio Overview', 'balance_chart', 'Portfolio Balance Trend', 'One row per month; sort_date, label, series, value in RUB bn.'),
    ('Portfolio Overview', 'quality_chart', 'Delinquency Trend', 'One row per month and DPD threshold; value in percentage points (6.94 means 6.94%).'),
    ('Portfolio Overview', 'product_chart', 'Portfolio Product Composition', 'One row per product; label, series, value in RUB bn.'),
    ('Portfolio Overview', 'region_table', 'Regional Performance', 'One row per region; balances in RUB and ratios as fractions; balance_label is in RUB bn.'),
    ('Sales and Funnel', 'sales_kpis', 'Sales KPIs', 'One row: current-month applications, approvals, disbursements and conversion.'),
    ('Sales and Funnel', 'sales_funnel_chart', 'Application Funnel', 'One row per stage; sort by stage; label, series, value in application counts.'),
    ('Sales and Funnel', 'sales_trend_chart', 'Disbursement Trend', 'One row per month; sort by month_end; value in RUB m.'),
    ('Sales and Funnel', 'sales_channel_chart', 'Disbursements by Channel', 'One row per channel; value in RUB m.'),
    ('Sales and Funnel', 'sales_plan_table', 'Sales Plan vs Actual', 'One row per product; funded and planned amounts in RUB; intentionally ignores Channel.'),
    ('Sales and Funnel', 'sales_channel_table', 'Channel Funnel Performance', 'One row per channel; application counts and formatted approval/conversion labels.'),
    ('Delinquency and Portfolio Quality', 'quality_kpis', 'Portfolio Quality KPIs', 'One row: overdue amounts, 31+/91+ ratios, past-due contracts, write-offs and registry count.'),
    ('Delinquency and Portfolio Quality', 'quality_buckets', 'DPD Bucket Exposure', 'One row per DPD bucket; value in RUB bn; active_loans is the contract count.'),
    ('Delinquency and Portfolio Quality', 'quality_transitions', 'DPD Transition Matrix', 'One row per from/to bucket; pivot by from_bucket and to_bucket; transition_ratio is a fraction.'),
    ('Delinquency and Portfolio Quality', 'quality_registry', 'Loan Registry', 'All matching active contracts, ordered by DPD descending then balance and loan ID; amounts in RUB.'),
    ('Vintage Analysis', 'vintage_kpis', 'Vintage KPIs', 'One row: original contract count and amount, cohort count and pooled mature MOB 3/6/12 ever-31+ ratios.'),
    ('Vintage Analysis', 'vintage_matrix', 'Vintage Matrix', 'One row per cohort and MOB 1-12; ever_ratio is a fraction; immature cells remain NULL.'),
    ('Vintage Analysis', 'vintage_curves', 'Vintage Curves', 'Four source-selected six-month-spaced cohorts (when available); value in percentage points; sort by mob.'),
    ('Loan Details', 'loan_kpis', 'Loan Details KPIs', 'One row with identity, balances, status and totals; follows Loan ID and As Of Month.'),
    ('Loan Details', 'loan_balance_chart', 'Loan Balance History', 'One row per observed month for the selected loan; value in RUB m.'),
    ('Loan Details', 'loan_dpd_chart', 'Loan DPD History', 'One row per observed month for the selected loan; value in days.'),
    ('Loan Details', 'loan_operations', 'Loan Operations', 'All operations for the selected loan through the selected cutoff; amounts in RUB.'),
    ('Loan Details', 'loan_schedule', 'Loan Payment Schedule', 'All effective installments for the selected loan; historical paid, written-off and overdue amounts in RUB.'),
]


def adapt(name, sql):
    sql = sql.strip().removesuffix(';')
    if name == 'quality_registry':
        start = sql.index('    registry_counts AS')
        end = sql.index('ordered AS', start)
        sql = sql[:start] + '    ' + sql[end:]
        sql = sql.replace('FROM ordered e CROSS JOIN paging p\n      WHERE e.registry_row_no BETWEEN (p.registry_page_no-1)*8+1 AND p.registry_page_no*8', 'FROM ordered e')
    elif name in ('loan_operations', 'loan_schedule'):
        start = sql.index(',\n      counts AS')
        end = sql.index(', ordered AS', start)
        sql = sql[:start] + sql[end:]
        alias, page = ('o', 'operation') if name == 'loan_operations' else ('s', 'schedule')
        sql = sql.replace(f'FROM ordered {alias} CROSS JOIN paging p\n      WHERE row_no BETWEEN (p.{page}_page_no-1)*8+1 AND p.{page}_page_no*8', f'FROM ordered {alias}')
    elif name == 'quality_kpis':
        start = sql.index('    registry_counts AS')
        end = sql.index(' summary AS', start)
        sql = sql[:start] + '    registry_counts AS (SELECT count(*) AS registry_total FROM eligible),' + sql[end:]
        sql = sql.replace('FROM summary s CROSS JOIN paging p', 'FROM summary s CROSS JOIN registry_counts p')
        start = sql.index("      'Page '||registry_page_no")
        end = sql.index('      CASE WHEN registry_total=0', start)
        sql = sql[:start] + sql[end:]
    elif name == 'vintage_kpis':
        start = sql.index(',\n      view_counts AS')
        end = sql.index('\n      SELECT t.*', start)
        sql = sql[:start] + sql[end:]
        start = sql.index(',p.matrix_page_count')
        sql = sql[:start] + '\n      FROM totals t CROSS JOIN rates r CROSS JOIN bounds b'
    elif name == 'loan_kpis':
        start = sql.index(',\n      page_counts AS')
        end = sql.index(' SELECT h.*,p.*', start)
        sql = sql[:start] + sql[end:]
        start = sql.index(',greatest(1,operation_page_no-1)')
        end = sql.index(' FROM paging p LEFT JOIN selected h ON true', start)
        sql = sql[:start] + sql[end:].replace('FROM paging p', 'FROM counts p', 1)
    assert not re.search(r'p_(?:quality_page|operation_page|schedule_page|vintage_page|vintage_mob_start)', sql), name
    return sql


def main():
    (OUT / 'sql').mkdir(parents=True, exist_ok=True)
    manifest = []
    for page, key, title, purpose in CATALOG:
        query = adapt(key, (ROOT / 'dashboard' / 'sql' / f'{key}.sql').read_text())
        params = {key: value for key, value in PARAMETERS.items() if '${INT(' + key + ')}' in query}
        assert set(re.findall(r'\$\{INT\((\w+)\)\}', query)) == set(params)
        header = f'-- Dataset: {title}\n-- Page: {page}\n-- Connection: CREDIT_PORTFOLIO | Mode: Direct\n'
        header += '-- Parameters: ' + (', '.join(f'{p} = {v["default"]} (Number)' for p, v in params.items()) or 'None') + '\n\n'
        path = 'sql/' + key + '.sql'
        (OUT / path).write_text(header + query + '\n')
        manifest.append(dict(name=title, key=key, page=page, file=path, parameters=params, purpose=purpose))
    (OUT / 'datasets.json').write_text(json.dumps(manifest, indent=2) + '\n')
    table = '\n'.join(f'| {i} | {d["page"]} | {d["name"]} | [{d["key"]}.sql]({d["file"]}) |' for i, d in enumerate(manifest, 1))
    param_table = '\n'.join(f'| `{p}` | {v["label"]} | Number | `{v["default"]}` |' for p, v in PARAMETERS.items())
    readme = '''# Credit Portfolio Analytics - FineBI SQL Datasets

28 PostgreSQL SELECT datasets for five native FineBI pages. All data is synthetic. Report labels are English and the reporting currency is RUB.

## Create datasets

1. Use the existing `Credit Portfolio` folder and `CREDIT_PORTFOLIO` connection. The source is `127.0.0.1:55433 / credit_portfolio_demo`, schema `credit`. No new database objects are required.
2. Create one SQL dataset for each catalog entry, using the exact English dataset name. `Overview KPIs` already exists: edit that dataset rather than creating a duplicate.
3. Use **Direct** mode for parameterized datasets. Extracted data is evaluated at extraction time and will not implement interactive SQL parameter filtering. Switching the data-list view is not proof that a particular existing dataset has changed mode; check the dataset/workbook behavior.
4. Paste the contents of the matching SQL file. Each file is a separate query. The files deliberately have no trailing semicolon. `${INT(p_date_key)}` and similar expressions are FineBI macros; paste them unchanged into FineBI, not a PostgreSQL console.
5. Click parameter **Refresh**, set the parameters actually present in that query to **Number**, and enter the defaults below. FineBI may initially suggest Text and `1`; replace those defaults. Dictionary datasets have no parameters.
6. Click **Preview**, then save. After adding the datasets to the workbook, configure SQL parameter bindings on the dashboard filters. Identical parameter names alone do not bind components automatically.
7. Each SQL file is self-contained. Do not join the 28 result datasets together. Add them independently to the workbook and choose the corresponding dataset for each component.

Official FineBI references: [SQL dataset creation](https://help.fanruan.com/finebi6.X/doc-view-890.html), [SQL parameters](https://help.fanruan.com/finebi6.X/doc-view-471.html), [Direct data](https://help.fanruan.com/finebi6.X/doc-view-85.html), [Filter parameter bindings](https://help.fanruan.com/finebi6.X/doc-view-1905.html).

## Parameters

| Parameter | Filter label | Type | Default |
|---|---|---|---|
''' + param_table + '''

`p_date_key` is an integer month-end key, not a Date parameter. `0` selects all products/regions/channels. `p_min_dpd=1` selects past-due active contracts in the registry only. `p_loan_id=0` shows the intentional no-selection state; use `2170` to preview a populated Loan Details page, then restore `0` for production defaults.

## Dataset catalog

Create the five filter dictionaries first, then the page datasets in the order below.

| # | Page | FineBI dataset name | SQL file |
|---|---|---|---|
''' + table + '''

## Filter bindings

| Dictionary dataset | Display field | Value field | SQL parameter |
|---|---|---|---|
| Filter - As Of Month | label | id | p_date_key |
| Filter - Product | label | id | p_product_id |
| Filter - Region | label | id | p_region_id |
| Filter - Channel | label | id | p_channel_id |
| Filter - Minimum DPD | label | id | p_min_dpd |

Use single-value selections. Bind a filter to every relevant dataset's SQL parameter in the workbook; the manifest lists the exact parameters for each dataset. FineBI 6.0.16+ supports binding one filter to multiple SQL parameters. On an earlier build, use the supported per-component parameter bindings or upgrade before assuming a shared filter controls all datasets.

`Loan Registry.loan_id` is the drill-through value for `p_loan_id`. Carry the selected `p_date_key` and portfolio filter context with the jump. Loan Details queries deliberately use only Loan ID and date; product/region/channel must be preserved as navigation/return context, not applied again to the selected contract.

## Field use, aggregation and units

- KPI datasets return one row. Use numeric fields for calculations; use `*_label` fields for preformatted display. `MAX` is safe for displaying a precomputed KPI or ratio; do not sum ratios across groups.
- Portfolio trend, product composition and DPD bucket `value` fields are in **RUB bn**. Disbursement trend, channel chart and Loan Balance History `value` fields are in **RUB m**. Loan DPD History values are in **days**. Loan Details KPI and table monetary fields are raw **RUB**.
- `Delinquency Trend.value` and `Vintage Curves.value` are **percentage points**: `6.94` means `6.94%`. Display a numeric value with a literal `%` suffix; a formatter that multiplies fractions by 100 would overstate them.
- Fields named `*_ratio`, `transition_ratio`, `ever_ratio`, `ratio31`, `ratio91`, and `plan_attainment` are **fractions**: `0.0694` means `6.94%`. Use standard percentage formatting.
- Tables generally expose raw RUB amounts plus text labels. `Regional Performance.balance_label` is already expressed in RUB bn; `balance` is raw RUB.
- For the transition pivot, rows = `from_bucket`, columns = `to_bucket`, value = `MAX(transition_ratio)`, formatted as percent. Sort using `from_order` and `to_order`. Each row's `opening_loans` repeats across seven cells; never sum it across the row. `SUM(loan_count)` is a count, not a transition percentage.
- For the vintage pivot, rows = `cohort_month` (descending), columns = `mob` (ascending), value = `MAX(ever_ratio)`, formatted as percent. Keep NULL as blank or an em dash. Immature cohorts must not become zero. `original_loan_count` and `original_amount` repeat across 12 MOB cells; do not sum them across MOBs. Use `Vintage KPIs` for portfolio totals.
- Chronological charts must sort by `sort_date`, `month_end`, `snapshot_date`, `stage`, or `mob` as appropriate, rather than alphabetically by the formatted labels.
- Loan Registry, Loan Operations and Loan Payment Schedule return **all matching rows**. Use FineBI's native table pagination/scrolling and explicit sort fields (`registry_row_no` or `row_no`). The old FineReport eight-row limit and page parameters have been removed. SQL has no LIMIT; check component row limits separately. FineBI editor previews can show only part of a dataset.

## Preserved metric definitions

- Overview balance is end-of-day principal. MTD disbursements follow the loan issue/funding date.
- Sales funnel follows applications submitted during the selected month, with outcomes known by the selected cutoff. It is a different population from funded-date disbursements.
- Sales Plan vs Actual follows month, product and region and intentionally covers all channels, because the source plan has no channel allocation.
- 31+/91+ DPD exposure is the entire outstanding principal of affected loans. Minimum DPD changes only the registry and its displayed count, not headline quality metrics or transitions.
- Vintage keeps closed and written-off contracts in original cohort denominators. Only fully mature, fully observed cohort/MOB cells have a ratio. Pooled MOB KPIs are weighted by original loan counts, not an average of cohort percentages. The curves retain the four source-selected cohorts rather than all 24 series.
- Loan operations stop at the selected cutoff. The effective payment schedule may contain future due installments, but paid, written-off, cancellation and closure information is evaluated as of the cutoff.

## Quick acceptance checks

With `p_date_key=20261031` and product/region/channel all `0`: Overview balance should display **RUB 19.55 bn**, MTD disbursements **RUB 800.88 m**, active borrowers **7,573**, monthly growth **2.52%**, 31+ DPD **6.94%**, 91+ DPD **4.95%**. Vintage Matrix should return **288 rows** (24 cohorts x 12 MOBs). With `p_loan_id=2170`, Loan Payment Schedule should return **36 rows**, rather than the old first eight installments.

Use `validation.json` for database-side results and parameter-specific row counts. Database validation expands FineBI macros to numbers and executes read-only PostgreSQL SELECTs; it does not replace checking parameter bindings and rendered components inside FineBI.
'''
    (OUT / 'README.md').write_text(readme)
    blocks = ['# Credit Portfolio Analytics - All SQL Queries\n\nOne block per FineBI SQL dataset. See README.md for parameter types, defaults and field units.\n']
    for d in manifest:
        blocks.append(f'## {d["name"]}\n\nPage: {d["page"]}\n\n```sql\n{(OUT / d["file"]).read_text().rstrip()}\n```\n')
    (OUT / 'ALL_DATASETS.md').write_text('\n'.join(blocks))
    print(f'Prepared {len(manifest)} datasets in {OUT}')


if __name__ == '__main__':
    main()
