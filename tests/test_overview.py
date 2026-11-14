import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
try:
    from overview import build_queries, expand
except ImportError:
    build_queries=expand=None


class OverviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_queries,'Overview dataset builder is not implemented')

    def fetch(self,sql):
        from local_database import environment
        env=environment(reader=True)
        result=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
            'SELECT coalesce(json_agg(r),\'[]\'::json) FROM ('+sql.strip().rstrip(';')+') r'],
            env=env,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)

    def test_overview_totals_match_delivered_fixture(self):
        row=self.fetch(expand(build_queries()['overview_kpis']['query']))[0]
        self.assertEqual(str(row['portfolio_balance']),'19550693343.27')
        self.assertEqual(row['active_borrowers'],7573)
        self.assertIn('19.55',row['portfolio_label'])

    def test_product_scope_matches_independent_balance(self):
        row=self.fetch(expand(build_queries()['overview_kpis']['query'],p_product_id=2))[0]
        direct=self.fetch("SELECT sum(s.principal_balance) balance FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) WHERE snapshot_date='2026-10-31' AND product_id=2")[0]
        self.assertEqual(row['portfolio_balance'],direct['balance'])

    def test_empty_scope_has_no_ratios_or_stale_labels(self):
        row=self.fetch(expand(build_queries()['overview_kpis']['query'],p_region_id=999))[0]
        self.assertEqual(row['portfolio_balance'],0)
        self.assertIsNone(row['dpd_31_plus_ratio'])
        self.assertEqual(row['ratio_31_label'],'—')
        self.assertEqual(row['scope_note'],'No loans match the selected filters.')

    def test_historical_month_has_correct_cutoff(self):
        row=self.fetch(expand(build_queries()['overview_kpis']['query'],p_date_key=20250831))[0]
        self.assertEqual(row['as_of_date'],'2025-08-31')
        self.assertEqual(len(self.fetch(expand(build_queries()['overview_trend']['query'],p_date_key=20250831))),10)

    def test_reject_untrusted_numeric_parameters(self):
        with self.assertRaises(ValueError):
            expand(build_queries()['overview_kpis']['query'],p_product_id='1;SELECT 2')


if __name__=='__main__':
    unittest.main()
