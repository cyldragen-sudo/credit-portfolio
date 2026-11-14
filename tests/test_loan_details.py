"""Independent PostgreSQL detail checks for dated contract drill-through."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
try:
    from loan_details import build_queries,expand
except ImportError:
    build_queries=expand=None


class LoanDetailsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_queries,'Loan detail datasets are not implemented')

    def fetch(self,sql):
        from local_database import environment
        env=environment(reader=True)
        r=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
            "SELECT coalesce(json_agg(r),'[]'::json) FROM ("+sql.strip().rstrip(';')+') r'],
            env=env,capture_output=True,text=True,check=True)
        return json.loads(r.stdout)

    def dataset(self,name,**params):
        return self.fetch(expand(build_queries()[name]['query'],**params))

    def test_summary_matches_snapshot_and_cash_ledger(self):
        row=self.dataset('loan_kpis',p_loan_id=2170)[0]
        direct=self.fetch("SELECT * FROM credit.loan_snapshot WHERE loan_id=2170 AND snapshot_date='2026-10-31'")[0]
        for name in ['principal_balance','overdue_principal','overdue_interest','dpd','loan_status']:
            self.assertEqual(row[name],direct[name])
        cash=self.fetch("SELECT sum(principal_amount+interest_amount) cash FROM credit.loan_operation WHERE loan_id=2170 AND operation_type IN ('REPAYMENT','PREPAYMENT') AND operation_date<='2026-10-31'")[0]
        self.assertEqual(row['cash_received'],cash['cash'])
        self.assertEqual(row['loan_reference'],'LN-0002170')

    def test_historical_closure_and_operations_do_not_leak_future(self):
        loan=self.fetch("SELECT loan_id FROM credit.loan WHERE issue_date<'2025-01-01' AND actual_close_date>'2025-01-31' AND actual_close_date<'2026-10-31' ORDER BY loan_id LIMIT 1")[0]['loan_id']
        early=self.dataset('loan_kpis',p_loan_id=loan,p_date_key=20250131)[0]
        final=self.dataset('loan_kpis',p_loan_id=loan)[0]
        self.assertIsNone(early['actual_close_date'])
        self.assertIsNone(early['close_reason'])
        self.assertIsNotNone(final['actual_close_date'])
        self.assertEqual(early['loan_status'],'Active')
        self.assertTrue(all(r['operation_date']<='2025-01-31' for r in self.dataset('loan_operations',p_loan_id=loan,p_date_key=20250131)))
        cash=self.fetch("SELECT coalesce(sum(principal_amount+interest_amount),0) n FROM credit.loan_operation WHERE loan_id="+str(loan)+" AND operation_type IN ('REPAYMENT','PREPAYMENT') AND operation_date<='2025-01-31'")[0]['n']
        self.assertEqual(early['cash_received'],cash)

    def test_schedule_uses_only_effective_contract_and_dated_allocations(self):
        rows=self.dataset('loan_schedule',p_loan_id=2170,p_date_key=20250831)
        direct=self.fetch("""SELECT a.installment_no,
          sum(a.allocated_amount) FILTER(WHERE o.operation_type<>'WRITE_OFF') paid,
          sum(a.allocated_amount) FILTER(WHERE o.operation_type='WRITE_OFF') written
          FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
          WHERE a.loan_id=2170 AND o.operation_date<='2025-08-31' GROUP BY 1""")
        by_no={r['installment_no']:r for r in direct}
        self.assertGreater(len(rows),0)
        for row in rows:
            expected=by_no.get(row['installment_no'],{})
            self.assertEqual(row['paid_amount'],expected.get('paid') or 0)
            self.assertEqual(row['written_off_amount'],expected.get('written') or 0)
            self.assertIsNone(row['cancelled_on'])

    def test_both_tables_are_stable_disjoint_and_bounded(self):
        loan=self.fetch("""SELECT l.loan_id FROM credit.loan l JOIN credit.loan_operation o USING(loan_id)
          WHERE l.term_months>16 GROUP BY l.loan_id HAVING count(*)>16 ORDER BY l.loan_id LIMIT 1""")[0]['loan_id']
        for table,param,prefix in [('loan_operations','p_operation_page','operation'),('loan_schedule','p_schedule_page','schedule')]:
            first=self.dataset(table,p_loan_id=loan,**{param:1})
            second=self.dataset(table,p_loan_id=loan,**{param:2})
            key='operation_id' if prefix=='operation' else 'installment_no'
            self.assertEqual(len(first),8)
            self.assertGreater(len(second),0)
            self.assertFalse({r[key] for r in first}&{r[key] for r in second})
            self.assertEqual(first,self.dataset(table,p_loan_id=loan,**{param:1}))
            last=self.dataset('loan_kpis',p_loan_id=loan,**{param:999999})[0]
            self.assertEqual(last[prefix+'_page_no'],last[prefix+'_page_count'])
            self.assertEqual(last[prefix+'_next_page'],last[prefix+'_page_count'])

    def test_history_is_chronological_and_ends_at_selected_date(self):
        for name in ['loan_balance_chart','loan_dpd_chart']:
            rows=self.dataset(name,p_loan_id=2170,p_date_key=20250831)
            self.assertGreater(len(rows),0)
            dates=[r['snapshot_date'] for r in rows]
            self.assertEqual(dates,sorted(dates))
            self.assertEqual(dates[-1],'2025-08-31')
            self.assertTrue(all('2024-11-01'<=d<='2025-08-31' for d in dates))
            self.assertTrue(all(r['value']>=0 for r in rows))

    def test_written_off_cash_excludes_debt_extinguishment(self):
        loan=self.fetch("SELECT l.loan_id FROM credit.loan l JOIN credit.loan_snapshot s USING(loan_id) WHERE s.snapshot_date='2026-10-31' AND s.loan_status='Written Off' ORDER BY l.loan_id LIMIT 1")[0]['loan_id']
        row=self.dataset('loan_kpis',p_loan_id=loan)[0]
        self.assertEqual(row['loan_status'],'Written Off')
        self.assertEqual(row['principal_balance'],0)
        direct=self.fetch("SELECT coalesce(sum(principal_amount+interest_amount) FILTER(WHERE operation_type IN ('REPAYMENT','PREPAYMENT')),0) cash, sum(principal_amount) FILTER(WHERE operation_type='WRITE_OFF') written FROM credit.loan_operation WHERE loan_id="+str(loan))[0]
        self.assertEqual(row['cash_received'],direct['cash'])
        self.assertGreater(direct['written'],0)

    def test_missing_unselected_and_unissued_loans_are_empty(self):
        future=self.fetch("SELECT loan_id FROM credit.loan WHERE issue_date>'2025-01-31' ORDER BY loan_id LIMIT 1")[0]['loan_id']
        for loan,date in [(0,20261031),(999999,20261031),(future,20250131)]:
            params=dict(p_loan_id=loan,p_date_key=date)
            k=self.dataset('loan_kpis',**params)[0]
            self.assertEqual(k['selected_loan_id'],0)
            self.assertEqual(k['balance_label'],'—')
            for name in ['loan_operations','loan_schedule','loan_balance_chart','loan_dpd_chart']:
                self.assertEqual(self.dataset(name,**params),[])

    def test_reject_unknown_noninteger_and_negative_parameters(self):
        for params in [dict(p_loan_id='2170'),dict(p_operation_page=-1),dict(p_fake=2)]:
            with self.assertRaises(ValueError):expand('SELECT 1',**params)


if __name__=='__main__':unittest.main()
