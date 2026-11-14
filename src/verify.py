#!/usr/bin/env python3
"""Independently reconcile the loaded fixture and execute every FineReport dataset."""
import csv
import io
import json
from pathlib import Path
import time

from database import ROOT, psql, scalar
from query_contract import render

CHECKS = {
    'schedule_principal_equals_original': """
        SELECT count(*) FROM (SELECT l.loan_id FROM credit.loan l JOIN credit.payment_schedule s USING(loan_id)
        GROUP BY l.loan_id,l.original_principal HAVING sum(s.principal_due)<>l.original_principal) x""",
    'operation_components_equal_allocations': """
        SELECT count(*) FROM credit.loan_operation o LEFT JOIN
        (SELECT operation_id,sum(allocated_amount) FILTER(WHERE component='Principal') p,
        sum(allocated_amount) FILTER(WHERE component='Interest') i FROM credit.payment_allocation GROUP BY operation_id) a USING(operation_id)
        WHERE o.operation_type<>'DISBURSEMENT'
        AND (o.principal_amount<>coalesce(a.p,0) OR o.interest_amount<>coalesce(a.i,0))""",
    'no_schedule_component_overallocation': """
        SELECT count(*) FROM credit.v_schedule_actual WHERE principal_paid+principal_written_off>principal_due
        OR interest_paid+interest_written_off>interest_due""",
    'all_daily_balances_reconcile_to_ledger': """
        WITH daily AS (
          SELECT loan_id,operation_date,sum(CASE WHEN operation_type='DISBURSEMENT'
          THEN principal_amount ELSE -principal_amount END) delta
          FROM credit.loan_operation GROUP BY loan_id,operation_date
        ), ledger AS (
          SELECT loan_id,operation_date,
          sum(delta) OVER(PARTITION BY loan_id ORDER BY operation_date) balance,
          lead(operation_date,1,(SELECT as_of_date+1 FROM credit.dataset_run))
          OVER(PARTITION BY loan_id ORDER BY operation_date) next_date FROM daily
        ) SELECT count(*) FROM credit.loan_snapshot s JOIN ledger l ON l.loan_id=s.loan_id
        AND s.snapshot_date>=l.operation_date AND s.snapshot_date<l.next_date
        WHERE s.principal_balance<>l.balance""",
    'snapshot_history_is_complete': """
        SELECT count(*) FROM credit.loan l CROSS JOIN credit.dataset_run r LEFT JOIN
        (SELECT loan_id,count(*) n,min(snapshot_date) first_day,max(snapshot_date) last_day
         FROM credit.loan_snapshot GROUP BY loan_id) s USING(loan_id)
        WHERE s.n IS NULL OR s.n<>r.as_of_date-greatest(l.issue_date,r.report_start-1)+1
        OR s.first_day<>greatest(l.issue_date,r.report_start-1) OR s.last_day<>r.as_of_date""",
    'current_dpd_and_overdue_reconcile_to_obligations': """
        WITH owed AS (
          SELECT s.loan_id,min(s.due_date) FILTER(WHERE
          s.principal_due-s.principal_paid-s.principal_written_off+
          s.interest_due-s.interest_paid-s.interest_written_off>0) first_unpaid,
          sum(s.principal_due-s.principal_paid-s.principal_written_off) p,
          sum(s.interest_due-s.interest_paid-s.interest_written_off) i
          FROM credit.v_schedule_actual s CROSS JOIN credit.dataset_run r
          WHERE s.due_date<r.as_of_date AND (s.cancelled_on IS NULL OR s.cancelled_on>r.as_of_date)
          GROUP BY s.loan_id
        ) SELECT count(*) FROM credit.loan_snapshot s CROSS JOIN credit.dataset_run r
        LEFT JOIN owed o USING(loan_id) WHERE s.snapshot_date=r.as_of_date
        AND (s.dpd<>coalesce(r.as_of_date-o.first_unpaid,0)
        OR s.overdue_principal<>coalesce(o.p,0) OR s.overdue_interest<>coalesce(o.i,0))""",
    'no_future_observations': """
        SELECT (SELECT count(*) FROM credit.loan_operation CROSS JOIN credit.dataset_run WHERE operation_date>as_of_date)
        +(SELECT count(*) FROM credit.loan_snapshot CROSS JOIN credit.dataset_run WHERE snapshot_date>as_of_date)
        +(SELECT count(*) FROM credit.loan_month_age CROSS JOIN credit.dataset_run WHERE observation_date>as_of_date)
        +(SELECT count(*) FROM credit.application_event CROSS JOIN credit.dataset_run WHERE event_date>as_of_date)""",
    'historical_dpd_and_overdue_reconcile': """
        WITH dates(day) AS (VALUES ('2024-12-31'::date),('2025-08-15'::date),('2026-06-30'::date)),
        allocated AS (
          SELECT d.day,a.loan_id,a.installment_no,
          coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Principal'),0) p,
          coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Interest'),0) i
          FROM dates d JOIN credit.loan_operation o ON o.operation_date<=d.day
          JOIN credit.payment_allocation a USING(operation_id)
          GROUP BY d.day,a.loan_id,a.installment_no
        ), owed AS (
          SELECT d.day,s.loan_id,
          min(s.due_date) FILTER(WHERE s.principal_due-coalesce(a.p,0)+s.interest_due-coalesce(a.i,0)>0) first_unpaid,
          sum(s.principal_due-coalesce(a.p,0)) p,sum(s.interest_due-coalesce(a.i,0)) i
          FROM dates d JOIN credit.payment_schedule s ON s.effective_from<=d.day AND s.due_date<d.day
          AND (s.cancelled_on IS NULL OR s.cancelled_on>d.day)
          LEFT JOIN allocated a ON a.day=d.day AND a.loan_id=s.loan_id AND a.installment_no=s.installment_no
          GROUP BY d.day,s.loan_id
        ) SELECT count(*) FROM credit.loan_snapshot s JOIN dates d ON d.day=s.snapshot_date
        LEFT JOIN owed o ON o.day=d.day AND o.loan_id=s.loan_id
        WHERE s.dpd<>coalesce(d.day-o.first_unpaid,0)
        OR s.overdue_principal<>coalesce(o.p,0) OR s.overdue_interest<>coalesce(o.i,0)""",
    'vintage_ever_flags_reconcile_to_payment_obligations': """
        WITH allocated AS (
          SELECT a.loan_id,a.installment_no,sum(a.allocated_amount) amount
          FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
          JOIN credit.payment_schedule s ON s.loan_id=a.loan_id AND s.installment_no=a.installment_no
          WHERE o.operation_date<=s.due_date+31 GROUP BY a.loan_id,a.installment_no
        ), first_event AS (
          SELECT s.loan_id,min(s.due_date+31) first_31_date
          FROM credit.payment_schedule s CROSS JOIN credit.dataset_run r
          LEFT JOIN allocated a ON a.loan_id=s.loan_id AND a.installment_no=s.installment_no
          WHERE s.due_date+31<=r.as_of_date AND (s.cancelled_on IS NULL OR s.cancelled_on>s.due_date+31)
          AND s.principal_due+s.interest_due>coalesce(a.amount,0) GROUP BY s.loan_id
        ) SELECT count(*) FROM credit.loan_month_age a LEFT JOIN first_event f USING(loan_id)
        WHERE a.ever_31_plus IS DISTINCT FROM coalesce(f.first_31_date<=a.observation_date,false)""",
    'closure_matches_zero_balance_and_ledger': """
        SELECT count(*) FROM credit.loan l JOIN credit.loan_snapshot s USING(loan_id)
        CROSS JOIN credit.dataset_run r WHERE s.snapshot_date=r.as_of_date
        AND ((l.actual_close_date IS NOT NULL)<>(s.loan_status<>'Active')
        OR (l.close_reason='Written Off')<>(s.loan_status='Written Off'))""",
    'ever_flag_is_monotonic': """
        SELECT count(*) FROM (SELECT ever_31_plus,lag(ever_31_plus) OVER(PARTITION BY loan_id ORDER BY snapshot_date) previous
        FROM credit.loan_snapshot) s WHERE previous AND NOT ever_31_plus""",
    'monthly_transitions_retain_entire_opening_cohort': """
        SELECT count(*) FROM (
        SELECT a.snapshot_date,count(*) n FROM credit.v_month_end_snapshot a CROSS JOIN credit.dataset_run r
        WHERE a.snapshot_date<date_trunc('month',r.as_of_date)::date GROUP BY 1
        EXCEPT SELECT from_date,count(*) FROM credit.v_monthly_transition GROUP BY 1) x""",
    'month_age_dates_are_true_anniversaries': """
        SELECT count(*) FROM credit.loan_month_age a JOIN credit.loan l USING(loan_id)
        WHERE observation_date<>(l.issue_date+make_interval(months=>a.months_on_book))::date""",
    'documented_objects': """
        SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='credit' AND c.relkind IN ('r','v') AND obj_description(c.oid,'pg_class') IS NULL""",
}


def rows(sql):
    sql = sql.strip().rstrip(';')
    result = psql('-q', '-c', 'COPY (' + sql + ') TO STDOUT WITH CSV HEADER', capture_output=True, text=True)
    return list(csv.DictReader(io.StringIO(result.stdout)))


def main():
    started = time.monotonic()
    destination = ROOT / 'validation'
    destination.mkdir(exist_ok=True)
    result = dict(database_version=scalar('SHOW server_version'), checks=[], datasets=[])
    manifest = json.loads((ROOT / 'data/generated/manifest.json').read_text())
    result['row_counts'] = {}
    for table, expected in manifest['rows'].items():
        actual = int(scalar('SELECT count(*) FROM credit.' + table))
        if actual != expected:
            raise AssertionError((table, expected, actual))
        result['row_counts'][table] = actual
    for name, sql in CHECKS.items():
        check_start = time.monotonic()
        failures = int(scalar(sql))
        print(name + ': ' + str(failures), flush=True)
        if failures:
            raise AssertionError(name + ': ' + str(failures) + ' inconsistent records')
        result['checks'].append(dict(name=name, inconsistent_records=failures,
                                     elapsed_seconds=round(time.monotonic()-check_start,2)))
    export_dir = ROOT / 'data/page-samples'
    export_dir.mkdir(exist_ok=True)
    for query in sorted((ROOT / 'queries').glob('*.sql')):
        contents = query.read_text()
        sql = render(contents)
        observed = rows(sql)
        # Execute both historical-as-of and empty filtered cases.
        historical = rows(render(contents, dict(p_as_of='2025-08-15',p_end='2025-08-15')))
        empty = rows(render(contents, dict(p_product_id=999999,p_loan_id=999999)))
        result['datasets'].append(dict(file=query.name, default_rows=len(observed),
                                       historical_rows=len(historical), empty_scope_rows=len(empty)))
        if observed:
            with (export_dir / (query.stem + '.csv')).open('w',newline='',encoding='utf-8') as stream:
                writer = csv.DictWriter(stream,fieldnames=list(observed[0]))
                writer.writeheader()
                writer.writerows(observed)
    vintage = rows(render((ROOT / 'queries/10_vintage.sql').read_text()))
    if any(row['cohort_month']=='2026-10-01' for row in vintage):
        raise AssertionError('Immature current-month vintages must be absent')
    result['checks'].append(dict(name='immature_vintage_cells_absent',inconsistent_records=0))
    result['sample_kpis'] = rows(render((ROOT / 'queries/01_overview_kpis.sql').read_text()))
    result['scenario_examples'] = rows("""
        SELECT DISTINCT ON (c.scenario_code) c.scenario_code,l.loan_id,l.loan_reference,s.loan_status,s.dpd
        FROM credit.simulation_scenario c JOIN credit.loan l USING(loan_id)
        JOIN credit.loan_snapshot s USING(loan_id) CROSS JOIN credit.dataset_run r
        WHERE s.snapshot_date=r.as_of_date ORDER BY c.scenario_code,s.dpd DESC,l.loan_id""")
    result['channel_quality'] = rows("""
        SELECT c.channel_name,date_trunc('year',l.issue_date)::date issue_year,
        count(*) original_loans,count(*) FILTER(WHERE a.ever_31_plus) ever_31_plus_at_mob6,
        count(*) FILTER(WHERE a.ever_31_plus)::numeric/count(*) ratio
        FROM credit.loan l JOIN credit.channel c USING(channel_id)
        JOIN credit.loan_month_age a ON a.loan_id=l.loan_id AND a.months_on_book=6
        GROUP BY 1,2 ORDER BY 1,2""")
    result['elapsed_seconds'] = round(time.monotonic()-started,2)
    (destination / 'database-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    # A real dictionary exported from the loaded PostgreSQL catalog.
    dictionary = rows("""
        SELECT c.table_name,c.column_name,c.data_type,c.is_nullable,
        coalesce(c.numeric_scale::text,'') numeric_scale,
        col_description(('credit.'||c.table_name)::regclass,c.ordinal_position) description
        FROM information_schema.columns c WHERE c.table_schema='credit'
        ORDER BY c.table_name,c.ordinal_position""")
    with (ROOT / 'docs/catalog.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dictionary[0]))
        writer.writeheader()
        writer.writerows(dictionary)
    print('Verified {} reconciliations and {} datasets in default, historical and empty scopes.'.format(
          len(result['checks']),len(result['datasets'])))


if __name__ == '__main__':
    main()
