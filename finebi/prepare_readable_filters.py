#!/usr/bin/env python3
"""Prepare label-aware FineBI SQL without changing the original handoff pack."""
import argparse
import datetime
import json
from pathlib import Path

from verify_datasets import DEFAULTS, MANIFEST, fetch

HERE = Path(__file__).resolve().parent
OUT = HERE / 'readable-filters'
VALUES = json.loads((OUT / 'values.json').read_text())
LABEL_DEFAULTS = dict(p_date_key='October 2026', p_product_id='All Products',
                      p_region_id='All Regions', p_channel_id='All Channels',
                      p_min_dpd='1+ DPD')
APPLIED = ['overview_kpis', 'balance_chart', 'quality_chart', 'product_chart', 'region_table']
APPLIED += ['sales_kpis', 'sales_funnel_chart', 'sales_trend_chart',
            'sales_channel_chart', 'sales_plan_table', 'sales_channel_table']
APPLIED += ['quality_kpis', 'quality_buckets', 'quality_transitions', 'quality_registry']
APPLIED += ['vintage_kpis', 'vintage_matrix', 'vintage_curves']
APPLIED += ['loan_kpis', 'loan_balance_chart', 'loan_dpd_chart',
            'loan_operations', 'loan_schedule']

JUMP_TARGET = ('http://localhost:37799/webroot/decision/v5/conf/subject/page/view/'
               '55f29d3962924a6692b2b3816cdafda6/report/f1e20436263842bb85acb6f4f88cb775')


def registry_jump_sql(sql):
    """Carry the requested filter values, including All, with the row's loan ID."""
    def encoded_label(param):
        cases = ' '.join(f"WHEN {entry['id']} THEN '{entry['label']}'" for entry in VALUES[param])
        label = f"(CASE ${{INT({param})}} {cases} END)"
        return f"replace(replace({label}, '+', '%2B'), ' ', '%20')"

    query = [f"'{JUMP_TARGET}?p_loan_id=' || registry.loan_id",
             "'&p_date_key=' || to_char(registry.snapshot_date, 'YYYYMMDD')"]
    for label, param in [('As%20Of%20Month', 'p_date_key'), ('Product', 'p_product_id'),
                         ('Region', 'p_region_id'), ('Channel', 'p_channel_id'),
                         ('Registry%20Threshold', 'p_min_dpd')]:
        query.append(f"'&{label}=' || {encoded_label(param)}")
    link = '\n      || '.join(query)
    return (f'WITH registry AS (\n{sql.strip()}\n)\n'
            f'SELECT registry.*, {link} AS loan_details_url\n'
            'FROM registry ORDER BY registry_row_no\n')


def expression(param):
    result = f'INT({param})'
    for entry in reversed(VALUES[param]):
        result = f'IF({param}={json.dumps(entry["label"])},{entry["id"]},{result})'
    return '${' + result + '}'


def prepare():
    specs = []
    for spec in MANIFEST:
        sql = (HERE / 'datasets' / spec['file']).read_text()
        if spec['key'] == 'quality_registry':
            sql = registry_jump_sql(sql)
        for param in VALUES:
            sql = sql.replace('${INT(' + param + ')}', expression(param))
        lines = sql.splitlines()
        lines = [line for line in lines if not line.startswith('-- Parameters:')]
        parameters = {}
        for param, definition in spec['parameters'].items():
            default = definition['default']
            parameters[param] = dict(type='Text' if param in VALUES else 'Number',
                                     default=LABEL_DEFAULTS.get(param, default))
        if parameters:
            lines.insert(3, '-- Parameters: ' + ', '.join(
                f'{p} = {v["default"]} ({v["type"]})' for p, v in parameters.items()))
        target = OUT / spec['file']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('\n'.join(lines) + '\n')
        specs.append(dict(spec, parameters=parameters, applied_in_finebi=spec['key'] in APPLIED))
    (OUT / 'datasets.json').write_text(json.dumps(specs, indent=2) + '\n')


def compile_labels(sql, params):
    # Only fixed generated macro expressions are accepted. No raw SQL interpolation.
    for param, entries in VALUES.items():
        value = params[param]
        mapping = {e['label']: e['id'] for e in entries}
        numeric = mapping[value] if value in mapping else int(value)
        sql = sql.replace(expression(param), str(numeric))
    return sql


def verify():
    scenarios = dict(
        default=LABEL_DEFAULTS,
        historical_segment=dict(p_date_key='August 2025', p_product_id='Personal Loan',
                                p_region_id='Moscow', p_channel_id='Online', p_loan_id=954),
        empty_segment_no_loan=dict(LABEL_DEFAULTS, p_region_id='999'),
        selected_loan_2170=dict(LABEL_DEFAULTS, p_loan_id=2170))
    records = []
    for scenario, overrides in scenarios.items():
        params = dict(DEFAULTS, **overrides)
        numeric = dict(params)
        for param, entries in VALUES.items():
            mapping = {e['label']: e['id'] for e in entries}
            numeric[param] = mapping[params[param]] if params[param] in mapping else int(params[param])
        for spec in MANIFEST:
            if scenario == 'selected_loan_2170' and spec['page'] != 'Loan Details':
                continue
            source = (HERE / 'datasets' / spec['file']).read_text()
            actual = fetch(compile_labels((OUT / spec['file']).read_text(), params), numeric)
            original = fetch(source, numeric)
            if spec['key'] == 'quality_registry':
                from urllib.parse import parse_qs, urlsplit
                for row in actual:
                    link = urlsplit(row['loan_details_url'])
                    assert link._replace(query='').geturl() == JUMP_TARGET
                    query = parse_qs(link.query)
                    assert query['p_loan_id'] == [str(row['loan_id'])]
                    assert query['p_date_key'] == [str(numeric['p_date_key'])]
                    for label, param in [('As Of Month', 'p_date_key'), ('Product', 'p_product_id'),
                                         ('Region', 'p_region_id'), ('Channel', 'p_channel_id'),
                                         ('Registry Threshold', 'p_min_dpd')]:
                        expected = next(e['label'] for e in VALUES[param] if e['id'] == numeric[param])
                        assert query[label] == [expected], (scenario, label)
                assert [{k: v for k, v in row.items() if k != 'loan_details_url'}
                        for row in actual] == original, (scenario, spec['key'])
            else:
                assert actual == original, (scenario, spec['key'])
            # Backward compatibility: numeric selections still compile identically.
            assert fetch(compile_labels((OUT / spec['file']).read_text(), numeric), numeric) == actual
            records.append(dict(scenario=scenario, dataset=spec['key'], rows=len(actual)))
        print(f'{scenario}: passed', flush=True)
    result = dict(verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  result='passed', scenario_dataset_checks=len(records),
                  scope='Read-only database parity after deterministic label macro compilation; '
                        'both English labels and numeric fallback. FineBI runtime checked separately.',
                  checks=records)
    (OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'PASS: {len(records)} dataset/scenario checks, English and numeric parameters')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    prepare()
    if args.verify:
        verify()
