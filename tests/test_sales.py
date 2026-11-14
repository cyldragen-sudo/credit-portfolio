import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from overview import expand
try:
    from sales import build_queries
except ImportError:
    build_queries=None


class SalesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_queries,'Sales datasets are not implemented')

    def fetch(self,sql):
        from local_database import environment
        env=environment(reader=True)
        result=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
            'SELECT coalesce(json_agg(r),\'[]\'::json) FROM ('+sql.strip().rstrip(';')+') r'],
            env=env,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)

    def dataset(self,name,**parameters):
        return self.fetch(expand(build_queries()[name]['query'],**parameters))

    def test_funding_matches_disbursement_ledger(self):
        row=self.dataset('sales_kpis')[0]
        self.assertEqual(row['funded_amount'],800880000.00)
        direct=self.fetch("SELECT count(*) n,sum(principal_amount) amount FROM credit.loan_operation WHERE operation_type='DISBURSEMENT' AND operation_date BETWEEN '2026-10-01' AND '2026-10-31'")[0]
        self.assertEqual(row['funded_loans'],direct['n'])
        self.assertEqual(row['funded_amount'],direct['amount'])

    def test_historical_cohort_matches_dated_events(self):
        row=self.dataset('sales_kpis',p_date_key=20250831)[0]
        direct=self.fetch("""SELECT count(*) submitted,
          count(*) FILTER(WHERE EXISTS(SELECT 1 FROM credit.application_event e WHERE e.application_id=a.application_id AND e.event_status='Approved' AND e.event_date<='2025-08-31')) approved,
          count(*) FILTER(WHERE EXISTS(SELECT 1 FROM credit.application_event e WHERE e.application_id=a.application_id AND e.event_status='Funded' AND e.event_date<='2025-08-31')) funded
          FROM credit.application a WHERE submitted_date BETWEEN '2025-08-01' AND '2025-08-31'""")[0]
        self.assertEqual(row['submitted_applications'],direct['submitted'])
        self.assertEqual(row['approved_applications'],direct['approved'])
        self.assertEqual(row['cohort_funded_applications'],direct['funded'])
        self.assertEqual(row['submitted_applications'],row['cohort_funded_applications']+row['declined_applications']+row['withdrawn_applications']+row['in_progress_applications'])

    def test_plan_ignores_channel_and_matches_target_grain(self):
        all_channels=self.dataset('sales_plan_table')
        partner=self.dataset('sales_plan_table',p_channel_id=4)
        self.assertEqual(all_channels,partner)
        direct=self.fetch("SELECT sum(planned_amount) amount FROM credit.sales_plan WHERE plan_month='2026-10-01'")[0]
        self.assertAlmostEqual(sum(r['planned_amount'] for r in all_channels),direct['amount'],places=2)

    def test_scoped_flow_matches_independent_operation_join(self):
        row=self.dataset('sales_kpis',p_product_id=2,p_region_id=1,p_channel_id=4)[0]
        direct=self.fetch("""SELECT count(*) n,coalesce(sum(o.principal_amount),0) amount
          FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
          WHERE o.operation_type='DISBURSEMENT' AND o.operation_date BETWEEN '2026-10-01' AND '2026-10-31'
          AND l.product_id=2 AND l.channel_id=4 AND b.region_id=1""")[0]
        self.assertEqual(row['funded_loans'],direct['n'])
        self.assertEqual(row['funded_amount'],direct['amount'])
        self.assertEqual(sum(r['submitted_applications'] for r in self.dataset('sales_channel_table',p_product_id=2,p_region_id=1,p_channel_id=4)),row['submitted_applications'])

    def test_empty_scope_returns_null_ratios_and_empty_charts(self):
        row=self.dataset('sales_kpis',p_region_id=999)[0]
        self.assertEqual(row['funded_loans'],0)
        self.assertIsNone(row['approval_ratio'])
        self.assertIsNone(row['average_funded_amount'])
        self.assertEqual(row['approval_label'],'—')
        for name in ('sales_funnel_chart','sales_channel_chart','sales_plan_table','sales_channel_table','sales_trend_chart'):
            self.assertEqual(self.dataset(name,p_region_id=999),[],name)

    def test_trend_stops_at_selected_month(self):
        rows=self.dataset('sales_trend_chart',p_date_key=20250831)
        self.assertEqual(len(rows),10)
        self.assertEqual(rows[-1]['month_end'],'2025-08-31')
        self.assertTrue(all(r['month_end']<='2025-08-31' for r in rows))


if __name__=='__main__':
    unittest.main()
