#!/usr/bin/env python3
"""Read-only execution and source parity checks for the manual FineBI handoff."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from local_database import environment

FOLDER = ROOT / 'finebi' / 'datasets'
MANIFEST = json.loads((FOLDER / 'datasets.json').read_text())
DEFAULTS = dict(p_date_key=20261031, p_product_id=0, p_region_id=0,
                p_channel_id=0, p_min_dpd=1, p_loan_id=0,
                p_quality_page=1, p_operation_page=1, p_schedule_page=1,
                p_vintage_page=1, p_vintage_mob_start=1)
ENV = environment(reader=True)


def expand(sql, params):
    expanded = re.sub(r'\$\{INT\((\w+)\)\}', lambda m: str(params[m[1]]), sql)
    assert '${' not in expanded
    return expanded.strip().rstrip(';')


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        assert key not in obj, f'Duplicate result column: {key}'
        obj[key] = value
    return obj


def fetch(sql, params):
    sql = expand(sql, params)
    result = subprocess.run([ENV['PSQL'], '-X', '-w', '-Atq', '-v', 'ON_ERROR_STOP=1'],
        input="SET statement_timeout='30s'; SELECT coalesce(json_agg(r),'[]'::json) FROM (\n" + sql + '\n) r;',
        env=ENV, capture_output=True, text=True, check=True)
    return json.loads(result.stdout, object_pairs_hook=unique_object)


def main():
    scenarios = {
        'default': {},
        'historical_segment': dict(p_date_key=20250831, p_product_id=1,
                                   p_region_id=1, p_channel_id=2, p_loan_id=954),
        'empty_segment_no_loan': dict(p_region_id=999),
        'selected_loan_2170': dict(p_loan_id=2170),
    }
    records, samples = [], {}
    for scenario, overrides in scenarios.items():
        params = dict(DEFAULTS, **overrides)
        results = {}
        for spec in MANIFEST:
            key = spec['key']
            if scenario == 'selected_loan_2170' and spec['page'] != 'Loan Details':
                continue
            sql = (FOLDER / spec['file']).read_text()
            assert not sql.rstrip().endswith(';'), key
            assert not re.search(r'p_(?:quality_page|operation_page|schedule_page|vintage_page|vintage_mob_start)', sql), key
            rows = fetch(sql, params)
            original = fetch((ROOT / 'dashboard' / 'sql' / (key + '.sql')).read_text(), params)
            if key in ('quality_registry', 'loan_operations', 'loan_schedule'):
                assert rows[:8] == original, (scenario, key, 'first page changed')
            else:
                assert len(rows) == len(original), (scenario, key, 'row count changed')
                for row, old in zip(rows, original):
                    assert set(row) <= set(old), (scenario, key, 'unexpected fields')
                    assert row == {col: old[col] for col in row}, (scenario, key, 'metric changed')
            results[key] = rows
            records.append(dict(scenario=scenario, dataset=spec['name'], key=key,
                                rows=len(rows), columns=list(rows[0]) if rows else [],
                                source_parity=True))
        if 'quality_registry' in results:
            assert len(results['quality_registry']) == results['quality_kpis'][0]['registry_total']
        if 'vintage_matrix' in results:
            assert len(results['vintage_matrix']) == 12 * results['vintage_kpis'][0]['cohort_count']
            for cell in results['vintage_matrix']:
                if cell['observation_status'] != 'Observed':
                    assert cell['ever_ratio'] is None and cell['ever_count'] is None
        if 'loan_kpis' in results:
            kpi = results['loan_kpis'][0]
            assert len(results['loan_operations']) == kpi['operation_count']
            assert len(results['loan_schedule']) == kpi['schedule_count']
        if scenario == 'default':
            assert results['overview_kpis'][0]['portfolio_balance'] == 19550693343.27
            assert results['overview_kpis'][0]['active_borrowers'] == 7573
            assert len(results['vintage_matrix']) == 288
            samples['default_overview'] = {key: results['overview_kpis'][0][key] for key in
                ('portfolio_label', 'funding_label', 'borrowers_label', 'growth_label', 'ratio_31_label', 'ratio_91_label')}
            samples['default_registry_rows'] = len(results['quality_registry'])
        if scenario == 'selected_loan_2170':
            assert len(results['loan_operations']) == 3
            assert len(results['loan_schedule']) == 36
        if scenario == 'historical_segment':
            assert len(results['loan_operations']) == 10
            assert len(results['loan_schedule']) == 36
        print(f'{scenario}: {len(results)} datasets executed; source parity and completeness checks passed', flush=True)
    report = dict(verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  connection='CREDIT_PORTFOLIO', database='credit_portfolio_demo',
                  role='credit_report_user', dataset_count=len(MANIFEST),
                  scenario_dataset_checks=len(records), result='passed',
                  scope='Read-only PostgreSQL execution with numeric macro substitution; FineBI UI binding not tested by this script',
                  samples=samples, checks=records)
    (FOLDER / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(records)} scenario/dataset checks across {len(MANIFEST)} SQL datasets')


if __name__ == '__main__':
    main()
