import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
try:
    from delinquency import build_queries,expand
except ImportError:
    build_queries=expand=None


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_queries,'Quality datasets are not implemented')

    def fetch(self,sql):
        from local_database import environment
        env=environment(reader=True)
        result=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
            'SELECT coalesce(json_agg(r),\'[]\'::json) FROM ('+sql.strip().rstrip(';')+') r'],
            env=env,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)

    def dataset(self,name,**params):
        return self.fetch(expand(build_queries()[name]['query'],**params))

    def test_cards_match_independent_snapshot_and_ledger_sums(self):
        row=self.dataset('quality_kpis')[0]
        self.assertEqual(row['overdue_principal'],185878893.27)
        self.assertEqual(row['overdue_interest'],168526708.29)
        self.assertEqual(row['exposure_31_plus'],1357400315.29)
        direct=self.fetch("""SELECT coalesce(sum(principal_amount),0) amount FROM credit.loan_operation
          WHERE operation_type='WRITE_OFF' AND operation_date BETWEEN '2026-10-01' AND '2026-10-31'""")[0]
        self.assertEqual(row['monthly_writeoffs'],direct['amount'])

    def test_buckets_reconcile_to_full_portfolio(self):
        row=self.dataset('quality_kpis')[0]
        buckets=self.dataset('quality_buckets')
        self.assertAlmostEqual(sum(r['value'] for r in buckets)*1000000000,row['portfolio_balance'],places=2)
        self.assertEqual(sum(r['active_loans'] for r in buckets),row['active_loans'])
        self.assertEqual([r['label'] for r in buckets],['0','1-30','31-60','61-90','91+'])

    def test_matrix_retains_opening_cohort_and_terminal_states(self):
        rows=self.dataset('quality_transitions')
        opening=self.fetch("SELECT count(*) n FROM credit.loan_snapshot WHERE snapshot_date='2026-09-30'")[0]['n']
        self.assertEqual(len(rows),49)
        self.assertEqual(sum(r['loan_count'] for r in rows),opening)
        self.assertTrue(any(r['from_bucket']=='Closed' and r['loan_count']>0 for r in rows))
        self.assertTrue(any(r['to_bucket']=='Written Off' and r['loan_count']>0 for r in rows))
        for source in {r['from_bucket'] for r in rows}:
            group=[r for r in rows if r['from_bucket']==source]
            self.assertEqual(sum(r['loan_count'] for r in group),group[0]['opening_loans'])
            if group[0]['opening_loans']:
                self.assertAlmostEqual(sum(r['transition_ratio'] for r in group),1,places=10)

    def test_threshold_changes_registry_only(self):
        low=self.dataset('quality_kpis',p_min_dpd=1)[0]
        high=self.dataset('quality_kpis',p_min_dpd=91)[0]
        for field in ['portfolio_balance','overdue_principal','exposure_31_plus','past_due_loans','monthly_writeoffs']:
            self.assertEqual(low[field],high[field])
        self.assertGreater(low['registry_total'],high['registry_total'])
        self.assertEqual(self.dataset('quality_transitions',p_min_dpd=1),self.dataset('quality_transitions',p_min_dpd=91))
        self.assertTrue(all(r['dpd']>=91 for r in self.dataset('quality_registry',p_min_dpd=91)))

    def test_registry_pages_are_stable_disjoint_and_bounded(self):
        one=self.dataset('quality_registry',p_quality_page=1)
        two=self.dataset('quality_registry',p_quality_page=2)
        self.assertEqual(len(one),8)
        self.assertEqual(len(two),8)
        self.assertFalse({r['loan_id'] for r in one}&{r['loan_id'] for r in two})
        self.assertEqual(one,self.dataset('quality_registry',p_quality_page=1))
        last=self.dataset('quality_kpis',p_quality_page=999999)[0]
        self.assertEqual(last['registry_page_no'],last['registry_page_count'])
        self.assertTrue(self.dataset('quality_registry',p_quality_page=999999))
        self.assertEqual(self.dataset('quality_registry',p_quality_page=0),one)

    def test_historical_scope_matches_direct_rows(self):
        params=dict(p_date_key=20250831,p_product_id=2,p_region_id=1,p_channel_id=4)
        row=self.dataset('quality_kpis',**params)[0]
        direct=self.fetch("""SELECT sum(s.principal_balance) balance,sum(s.overdue_principal) overdue
          FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
          WHERE snapshot_date='2025-08-31' AND l.product_id=2 AND l.channel_id=4 AND b.region_id=1""")[0]
        self.assertEqual(row['portfolio_balance'],direct['balance'])
        self.assertEqual(row['overdue_principal'],direct['overdue'])
        self.assertEqual(row['as_of_date'],'2025-08-31')
        self.assertTrue(all(r['snapshot_date']=='2025-08-31' for r in self.dataset('quality_registry',**params)))

    def test_empty_scope_clears_cards_matrix_and_registry(self):
        row=self.dataset('quality_kpis',p_region_id=999,p_quality_page=99)[0]
        self.assertEqual(row['registry_total'],0)
        self.assertEqual(row['registry_page_no'],1)
        self.assertEqual(row['registry_page_count'],1)
        self.assertIsNone(row['dpd_31_plus_ratio'])
        self.assertEqual(row['ratio31_label'],'—')
        self.assertEqual(self.dataset('quality_buckets',p_region_id=999),[])
        self.assertEqual(self.dataset('quality_registry',p_region_id=999),[])
        matrix=self.dataset('quality_transitions',p_region_id=999)
        self.assertTrue(all(r['loan_count']==0 and r['transition_ratio'] is None for r in matrix))

    def test_registry_numeric_parameters_reject_untrusted_text(self):
        with self.assertRaises(ValueError):
            expand(build_queries()['quality_registry']['query'],p_min_dpd='1;SELECT 2')


if __name__=='__main__':
    unittest.main()
