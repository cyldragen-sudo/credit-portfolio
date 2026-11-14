"""Hand-calculated contracts: money, allocation, closure and DPD boundaries."""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
try:
    from ledger import add_months, schedule, simulate
except ImportError:
    add_months = schedule = simulate = None

D = dt.date.fromisoformat


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(simulate, 'Installment ledger has not been implemented')
        self.rows = [
            dict(installment_no=1, due_date=D('2024-02-01'), principal_cents=10000, interest_cents=1000),
            dict(installment_no=2, due_date=D('2024-03-01'), principal_cents=10000, interest_cents=900),
        ]

    def run_loan(self, payments=(), end='2024-03-03', **kw):
        return simulate(self.rows, payments, D(end), D('2024-01-01'), **kw)

    def test_calendar_and_principal_reconcile(self):
        self.assertEqual(add_months(D('2024-01-31'), 1), D('2024-02-29'))
        rows = schedule(10000, '0', 3, D('2024-01-31'))
        self.assertEqual([r['principal_cents'] for r in rows], [3333, 3333, 3334])
        rows = schedule(10000000, '18.5', 36, D('2024-01-31'))
        self.assertEqual(sum(r['principal_cents'] for r in rows), 10000000)
        self.assertTrue(all(r['principal_cents'] > 0 for r in rows))

    def test_unpaid_due_day_is_not_overdue(self):
        result = self.run_loan(end='2024-02-02')
        by_day = {r['snapshot_date']: r for r in result['snapshots']}
        self.assertEqual(by_day[D('2024-02-01')]['dpd'], 0)
        self.assertEqual(by_day[D('2024-02-02')]['dpd'], 1)
        self.assertEqual(by_day[D('2024-02-02')]['overdue_principal_cents'], 10000)

    def test_partial_payment_leaves_interest_and_ages(self):
        result = self.run_loan([(D('2024-02-01'), 500, 'REPAYMENT')])
        last = result['snapshots'][-1]
        self.assertEqual(last['principal_cents'], 20000)
        self.assertEqual(last['overdue_interest_cents'], 1400)
        self.assertEqual(last['dpd'], 31)
        self.assertEqual(last['bucket'], '31-60')
        self.assertEqual(result['operations'][0]['interest_cents'], 500)

    def test_cure_pays_oldest_obligation(self):
        result = self.run_loan([(D('2024-03-04'), 21900, 'REPAYMENT')], end='2024-03-04')
        last = result['snapshots'][-1]
        self.assertEqual((last['principal_cents'], last['dpd'], last['status']), (0, 0, 'Closed'))
        self.assertEqual(result['closed_date'], D('2024-03-04'))
        self.assertTrue(result['snapshots'][-2]['ever_31_plus'])

    def test_prepayment_cancels_future_interest(self):
        result = self.run_loan([(D('2024-02-10'), None, 'PREPAYMENT')])
        operation = result['operations'][0]
        self.assertEqual((operation['principal_cents'], operation['interest_cents']), (20000, 1000))
        self.assertEqual(result['snapshots'][-1]['principal_cents'], 0)
        self.assertEqual(result['closed_date'], D('2024-02-10'))

    def test_writeoff_is_separate_from_repayment(self):
        result = self.run_loan(writeoff_date=D('2024-03-02'))
        operation = result['operations'][0]
        self.assertEqual(operation['type'], 'WRITE_OFF')
        self.assertEqual((operation['principal_cents'], operation['interest_cents']), (20000, 1900))
        self.assertEqual(result['snapshots'][-1]['status'], 'Written Off')

    def test_future_payment_does_not_change_history(self):
        result = self.run_loan([(D('2024-04-01'), None, 'PREPAYMENT')])
        self.assertEqual(result['operations'], [])
        self.assertEqual(result['snapshots'][-1]['principal_cents'], 20000)

    def test_reject_overpayment(self):
        with self.assertRaises(ValueError):
            self.run_loan([(D('2024-02-01'), 999999, 'REPAYMENT')])


if __name__ == '__main__':
    unittest.main()
