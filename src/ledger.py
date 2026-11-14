"""Exact-money synthetic installment ledger; all internal amounts are kopecks."""
import calendar
import datetime as dt
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def add_months(day, months):
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    return dt.date(year, month + 1, min(day.day, calendar.monthrange(year, month + 1)[1]))


def schedule(principal_cents, annual_rate, term_months, issue_date):
    if principal_cents <= 0 or term_months <= 0 or Decimal(annual_rate) < 0:
        raise ValueError('Positive principal/term and nonnegative interest are required')
    rate = Decimal(annual_rate) / Decimal(1200)
    principal = Decimal(principal_cents)
    payment = (principal / term_months if not rate else
               principal * rate / (1 - (1 + rate) ** (-term_months)))
    payment = int(payment.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    balance, rows = principal_cents, []
    for number in range(1, term_months + 1):
        interest = int((Decimal(balance) * rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        paid_principal = balance if number == term_months else min(balance, payment - interest)
        if paid_principal <= 0:
            raise ValueError('Rounded installment cannot amortize this principal')
        rows.append(dict(installment_no=number, due_date=add_months(issue_date, number),
                         principal_cents=paid_principal, interest_cents=interest))
        balance -= paid_principal
    return rows


def simulate(schedule_rows, payment_events, as_of, snapshot_start, writeoff_date=None):
    """Apply (date, amount-or-None, type) events and emit end-of-day states.

    None is allowed for PREPAYMENT: outstanding principal plus due interest.
    No unearned future interest is received. WRITE_OFF allocations extinguish
    debt but do not count as cash receipts. Future events never affect history.
    """
    rows = [dict(row, p=row['principal_cents'], i=row['interest_cents']) for row in schedule_rows]
    if not rows:
        raise ValueError('A nonempty schedule is required')
    events = defaultdict(list)
    for day, amount, kind in payment_events:
        if kind not in ('REPAYMENT', 'PREPAYMENT'):
            raise ValueError('Unsupported payment type')
        if day <= as_of:
            events[day].append((amount, kind))
    if writeoff_date and writeoff_date <= as_of:
        events[writeoff_date].append((None, 'WRITE_OFF'))
    balance = sum(row['p'] for row in rows)
    day = min([snapshot_start, rows[0]['due_date']] + list(events))
    snapshots, operations, closed_date = [], [], None
    status, ever = 'Active', False
    due_count = 0
    while day <= as_of:
        while due_count < len(rows) and rows[due_count]['due_date'] <= day:
            due_count += 1
        for amount, kind in events.get(day, ()):
            if status != 'Active':
                continue
            due_interest = sum(row['i'] for row in rows[:due_count])
            permitted = balance + due_interest if kind != 'REPAYMENT' else sum(
                row['p'] + row['i'] for row in rows[:due_count])
            if amount is None:
                if kind == 'REPAYMENT':
                    raise ValueError('Repayment must specify an amount')
                amount = permitted
            if amount <= 0 or amount > permitted:
                raise ValueError('Payment exceeds eligible debt or is not positive')
            remaining, paid_p, paid_i, allocations = amount, 0, 0, []
            for row in rows[:due_count]:
                for key, component in (('i', 'Interest'), ('p', 'Principal')):
                    paid = min(remaining, row[key])
                    if paid:
                        row[key] -= paid
                        remaining -= paid
                        paid_p += paid if key == 'p' else 0
                        paid_i += paid if key == 'i' else 0
                        allocations.append((row['installment_no'], component, paid))
            if kind in ('PREPAYMENT', 'WRITE_OFF'):
                for row in rows[due_count:]:
                    paid = min(remaining, row['p'])
                    if paid:
                        row['p'] -= paid
                        remaining -= paid
                        paid_p += paid
                        allocations.append((row['installment_no'], 'Principal', paid))
            if remaining:
                raise ValueError('Unallocated payment')
            balance -= paid_p
            operations.append(dict(date=day, type=kind, principal_cents=paid_p,
                                   interest_cents=paid_i, allocations=allocations))
            if balance == 0:
                status = 'Written Off' if kind == 'WRITE_OFF' else 'Closed'
                closed_date = day
        past_due = [row for row in rows[:due_count] if row['due_date'] < day and row['p'] + row['i'] > 0]
        dpd = (day - past_due[0]['due_date']).days if status == 'Active' and past_due else 0
        ever = ever or dpd >= 31
        bucket = ('0' if dpd == 0 else '1-30' if dpd <= 30 else '31-60' if dpd <= 60
                  else '61-90' if dpd <= 90 else '91+')
        if day >= snapshot_start:
            snapshots.append(dict(snapshot_date=day, principal_cents=balance,
                                  overdue_principal_cents=sum(row['p'] for row in past_due) if status == 'Active' else 0,
                                  overdue_interest_cents=sum(row['i'] for row in past_due) if status == 'Active' else 0,
                                  dpd=dpd, bucket=bucket, status=status, ever_31_plus=ever))
        day += dt.timedelta(days=1)
    return dict(operations=operations, snapshots=snapshots, closed_date=closed_date,
                status=status, schedule=rows)
