#!/usr/bin/env python3
"""Generate deterministic PostgreSQL COPY data. Python 3.9+, standard library only."""
import argparse
import calendar
from collections import Counter, defaultdict
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import shutil
import tempfile

from ledger import add_months, schedule, simulate

AS_OF = dt.date(2026, 10, 31)
HISTORY_START = dt.date(2023, 11, 1)
REPORT_START = dt.date(2024, 11, 1)
BASELINE = REPORT_START - dt.timedelta(days=1)
TABLES = {
    'dataset_run': 'run_id seed history_start report_start as_of_date loan_count is_synthetic generator_version',
    'region': 'region_id region_name', 'branch': 'branch_id branch_name region_id',
    'product': 'product_id product_name', 'channel': 'channel_id channel_name',
    'calendar': 'calendar_date month_start month_end year_number month_number',
    'customer': 'customer_id customer_label segment region_id relationship_start',
    'application': 'application_id customer_id product_id channel_id branch_id submitted_date requested_amount approved_date funded_date terminal_date outcome',
    'application_event': 'application_id event_date event_sequence event_status',
    'loan': 'loan_id loan_reference application_id customer_id product_id channel_id branch_id issue_date original_principal annual_rate term_months maturity_date currency risk_at_origination actual_close_date close_reason',
    'simulation_scenario': 'loan_id scenario_code scenario_description',
    'payment_schedule': 'loan_id schedule_version installment_no effective_from due_date principal_due interest_due cancelled_on',
    'loan_operation': 'operation_id loan_id operation_date operation_type principal_amount interest_amount',
    'payment_allocation': 'allocation_id operation_id loan_id schedule_version installment_no component allocated_amount',
    'loan_snapshot': 'snapshot_date loan_id principal_balance overdue_principal overdue_interest dpd dpd_bucket loan_status ever_31_plus',
    'loan_month_age': 'loan_id months_on_book observation_date ever_31_plus',
    'sales_plan': 'plan_month product_id branch_id planned_amount planned_count',
}
SCENARIOS = {
    'ON_TIME': 'Scheduled installments paid on the due date.',
    'SHORT_DELAY': 'Installments paid 5 to 20 days after the due date.',
    'CURE': 'Three installments delayed by 75 days; subsequent catch-up.',
    'PERSISTENT_ARREARS': 'Payments stop after an initial performing period.',
    'EARLY_SETTLEMENT': 'Outstanding principal and due interest settled early.',
    'WRITE_OFF': 'Persistent arrears followed by an explicit principal write-off.',
}


def money(cents):
    return '{}.{:02d}'.format(cents // 100, cents % 100)


class Spool:
    def __init__(self, directory):
        self.files, self.writers, self.counts = {}, {}, Counter()
        for table in TABLES:
            stream = (directory / (table + '.tsv')).open('w', newline='', encoding='utf-8')
            self.files[table] = stream
            self.writers[table] = csv.writer(stream, delimiter='\t', lineterminator='\n')

    def row(self, table, *values):
        if len(values) != len(TABLES[table].split()):
            raise ValueError('Column mismatch for ' + table)
        self.writers[table].writerow('\\N' if v is None else
                                   't' if v is True else 'f' if v is False else str(v) for v in values)
        self.counts[table] += 1

    def close(self):
        for stream in self.files.values():
            stream.close()


def generate(output, loan_count=12000, seed=20261104):
    if loan_count < 1:
        raise ValueError('Loan count must be positive')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Output directory must be empty; existing data will not be overwritten')
    rng = random.Random(seed)
    with tempfile.TemporaryDirectory(prefix='credit-spool-') as temporary:
        work = Path(temporary)
        spool = Spool(work)
        put = spool.row
        put('dataset_run', 1, seed, HISTORY_START, REPORT_START, AS_OF, loan_count, True, '1.0.0')
        regions = ['Moscow', 'Saint Petersburg', 'Tatarstan', 'Sverdlovsk Region', 'Krasnodar Region', 'Novosibirsk Region']
        for region_id, name in enumerate(regions, 1):
            put('region', region_id, name)
            for local in range(1, 4):
                branch = (region_id - 1) * 3 + local
                put('branch', branch, '{} Branch {:02d}'.format(name, local), region_id)
        for key, name in enumerate(['Personal Loan', 'Auto Loan', 'Mortgage'], 1):
            put('product', key, name)
        for key, name in enumerate(['Branch', 'Online', 'Mobile App', 'Partner'], 1):
            put('channel', key, name)
        day = dt.date(2023, 1, 1)
        while day <= dt.date(2050, 12, 31):
            month_end = day.replace(day=calendar.monthrange(day.year, day.month)[1])
            put('calendar', day, day.replace(day=1), month_end, day.year, day.month)
            day += dt.timedelta(days=1)
        customers = max(50, int(loan_count * 1.25))
        for key in range(1, customers + 1):
            put('customer', key, 'Customer {:06d}'.format(key), rng.choice(['Standard', 'Salary', 'Premium']),
                rng.randint(1, 6), dt.date(2020, 1, 1) + dt.timedelta(days=rng.randrange(1300)))
        issue_months = [add_months(HISTORY_START, n) for n in range(36)]
        month_weights = [(1 + n * .022) * (1.4 if d.month == 12 else .85 if d.month == 1 else 1)
                         for n, d in enumerate(issue_months)]
        operation_id = allocation_id = 0
        scenario_counts, actual_sales = Counter(), defaultdict(lambda: [0, 0])

        def application(key, customer, product, channel, branch, submitted, amount,
                        approved=None, funded=None, terminal=None, outcome='Funded'):
            put('application', key, customer, product, channel, branch, submitted, money(amount),
                approved, funded, terminal, outcome)
            events = [(submitted, 'Submitted')]
            if approved:
                events.append((approved, 'Approved'))
            if funded:
                events.append((funded, 'Funded'))
            elif terminal:
                events.append((terminal, outcome))
            for number, (event_day, status) in enumerate(events, 1):
                put('application_event', key, event_day, number, status)

        for loan_id in range(1, loan_count + 1):
            month = rng.choices(issue_months, month_weights)[0]
            issued = month.replace(day=rng.randint(1, calendar.monthrange(month.year, month.month)[1]))
            product = rng.choices([1, 2, 3], [.60, .25, .15])[0]
            channel = rng.choices([1, 2, 3, 4], [.30, .25, .25, .20])[0]
            branch, customer = rng.randint(1, 18), rng.randint(1, customers)
            if product == 1:
                principal, rate, term = rng.randrange(100000, 1500001, 10000) * 100, rng.choice(['17.9', '21.9', '25.9']), rng.choice([24, 36, 48, 60])
            elif product == 2:
                principal, rate, term = rng.randrange(700000, 4000001, 50000) * 100, rng.choice(['12.9', '16.9', '19.9']), rng.choice([36, 48, 60, 72])
            else:
                principal, rate, term = rng.randrange(2500000, 12000001, 100000) * 100, rng.choice(['8.5', '12.5', '16.5']), rng.choice([120, 180, 240])
            risk = rng.choices(['Low', 'Medium', 'High'], [.55, .32, .13])[0]
            adverse = channel == 4 and issued >= dt.date(2025, 7, 1)
            default_probability = (.025 if risk == 'Low' else .075 if risk == 'Medium' else .18) + (.18 if adverse else 0)
            draw = rng.random()
            if draw < default_probability:
                scenario = 'WRITE_OFF' if rng.random() < .35 else 'PERSISTENT_ARREARS'
            elif draw < default_probability + .10:
                scenario = 'CURE'
            elif draw < default_probability + .22:
                scenario = 'SHORT_DELAY'
            elif draw < default_probability + .34:
                scenario = 'EARLY_SETTLEMENT'
            else:
                scenario = 'ON_TIME'
            rows = schedule(principal, rate, term, issued)
            payment_events, writeoff = [], None
            stop_after, cure_start = rng.randint(2, 7), rng.randint(2, 6)
            early_month = rng.randint(6, min(18, term - 1))
            delay = rng.randint(5, 20)
            for row in rows:
                number, due = row['installment_no'], row['due_date']
                if scenario in ('PERSISTENT_ARREARS', 'WRITE_OFF') and number > stop_after:
                    continue
                if scenario == 'EARLY_SETTLEMENT' and number >= early_month:
                    continue
                lag = delay if scenario == 'SHORT_DELAY' else 75 if scenario == 'CURE' and cure_start <= number < cure_start + 3 else 0
                payment_events.append((due + dt.timedelta(days=lag), row['principal_cents'] + row['interest_cents'], 'REPAYMENT'))
            if scenario == 'EARLY_SETTLEMENT':
                payment_events.append((add_months(issued, early_month), None, 'PREPAYMENT'))
            if scenario == 'WRITE_OFF':
                writeoff = add_months(issued, stop_after + 1) + dt.timedelta(days=210)
            result = simulate(rows, sorted(payment_events, key=lambda e: e[0]), AS_OF, issued, writeoff)
            close = result['closed_date']
            reason = None if not close else 'Written Off' if result['status'] == 'Written Off' else 'Early Settlement' if scenario == 'EARLY_SETTLEMENT' else 'Repaid'
            submitted = issued - dt.timedelta(days=rng.randint(2, 10))
            approved = submitted + dt.timedelta(days=1)
            application(loan_id, customer, product, channel, branch, submitted, principal, approved, issued)
            put('loan', loan_id, 'LN-{:07d}'.format(loan_id), loan_id, customer, product, channel, branch,
                issued, money(principal), rate, term, rows[-1]['due_date'], 'RUB', risk, close, reason)
            put('simulation_scenario', loan_id, scenario, SCENARIOS[scenario])
            scenario_counts[scenario] += 1
            for row in rows:
                cancelled = close if close and row['due_date'] > close else None
                put('payment_schedule', loan_id, 1, row['installment_no'], issued, row['due_date'],
                    money(row['principal_cents']), money(row['interest_cents']), cancelled)
            operation_id += 1
            put('loan_operation', operation_id, loan_id, issued, 'DISBURSEMENT', money(principal), '0.00')
            for operation in result['operations']:
                operation_id += 1
                put('loan_operation', operation_id, loan_id, operation['date'], operation['type'],
                    money(operation['principal_cents']), money(operation['interest_cents']))
                for installment, component, amount in operation['allocations']:
                    allocation_id += 1
                    put('payment_allocation', allocation_id, operation_id, loan_id, 1, installment, component, money(amount))
            states = {}
            for state in result['snapshots']:
                day = state['snapshot_date']
                states[day] = state['ever_31_plus']
                if day >= BASELINE:
                    put('loan_snapshot', day, loan_id, money(state['principal_cents']),
                        money(state['overdue_principal_cents']), money(state['overdue_interest_cents']),
                        state['dpd'], state['bucket'], state['status'], state['ever_31_plus'])
            age = 1
            while add_months(issued, age) <= AS_OF:
                observed = add_months(issued, age)
                put('loan_month_age', loan_id, age, observed, states[observed])
                age += 1
            if issued >= REPORT_START:
                key = (issued.replace(day=1), product, branch)
                actual_sales[key][0] += principal
                actual_sales[key][1] += 1
            if loan_id % 2000 == 0:
                print('Simulated {:,} loans'.format(loan_id), flush=True)

        for number in range(1, max(30, int(loan_count * .60)) + 1):
            key = loan_count + number
            customer, product, channel, branch = rng.randint(1, customers), rng.randint(1, 3), rng.randint(1, 4), rng.randint(1, 18)
            outcome = rng.choices(['Declined', 'Withdrawn', 'Pending', 'Approved'], [.55, .30, .10, .05])[0]
            submitted = AS_OF - dt.timedelta(days=rng.randint(0, 12)) if outcome in ('Pending', 'Approved') else HISTORY_START + dt.timedelta(days=rng.randrange((AS_OF - HISTORY_START).days))
            terminal = min(submitted + dt.timedelta(days=rng.randint(1, 7)), AS_OF) if outcome in ('Declined', 'Withdrawn') else None
            approved = min(submitted + dt.timedelta(days=1), AS_OF) if outcome == 'Approved' or outcome == 'Withdrawn' and rng.random() < .5 else None
            if approved and terminal:
                terminal = max(approved, terminal)
            application(key, customer, product, channel, branch, submitted, rng.randrange(100000, 3000001, 10000) * 100,
                        approved=approved, terminal=terminal, outcome=outcome)
        for month in [add_months(REPORT_START, n) for n in range(24)]:
            for product in (1, 2, 3):
                for branch in range(1, 19):
                    amount, count = actual_sales[(month, product, branch)]
                    factor = rng.uniform(.85, 1.20)
                    put('sales_plan', month, product, branch, money(max(10000000, int(amount * factor))), max(1, round(count * factor)))
        spool.close()
        fixture = output / '002_demo_data.sql.gz'
        with fixture.open('wb') as binary:
            with gzip.GzipFile(fileobj=binary, mode='wb', filename='', mtime=0, compresslevel=6) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='\n') as stream:
                    stream.write('-- Fully synthetic deterministic fixture; all money in RUB.\n')
                    for table, columns in TABLES.items():
                        stream.write("COPY credit.{} ({}) FROM stdin WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N');\n".format(table, ', '.join(columns.split())))
                        with (work / (table + '.tsv')).open(encoding='utf-8') as source:
                            shutil.copyfileobj(source, stream)
                        stream.write('\\.\n')
        manifest = dict(generator_version='1.0.0', seed=seed, is_synthetic=True,
                        history_start=str(HISTORY_START), report_start=str(REPORT_START), as_of_date=str(AS_OF),
                        currency='RUB', rows=dict(spool.counts), scenarios=dict(scenario_counts),
                        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest())
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loans', type=int, default=12000)
    parser.add_argument('--seed', type=int, default=20261104)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/generated')
    args = parser.parse_args()
    generate(args.output, args.loans, args.seed)
