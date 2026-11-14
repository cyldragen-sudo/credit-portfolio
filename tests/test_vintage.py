"""Real PostgreSQL checks for native cohort maturity and original denominators."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
try:
    from vintage import build_queries,expand
except ImportError:
    build_queries=expand=None


class VintageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_queries,'Vintage datasets are not implemented')

    def fetch(self,sql):
        from local_database import environment
        env=environment(reader=True)
        r=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
            "SELECT coalesce(json_agg(r),'[]'::json) FROM ("+sql.strip().rstrip(';')+') r'],
            env=env,capture_output=True,text=True,check=True)
        return json.loads(r.stdout)

    def dataset(self,name,**params):
        return self.fetch(expand(build_queries()[name]['query'],**params))

    def test_matrix_reconciles_to_original_cohorts_and_anniversaries(self):
        rows=self.dataset('vintage_matrix')
        self.assertEqual(len(rows),24*12)
        direct=self.fetch("""SELECT date_trunc('month',l.issue_date)::date cohort_month,m.mob,
          count(*) n,sum(l.original_principal) amount,
          max((l.issue_date+make_interval(months=>m.mob))::date) maturity,
          count(*) FILTER(WHERE a.ever_31_plus) ever
          FROM credit.loan l CROSS JOIN generate_series(1,12) m(mob)
          LEFT JOIN credit.loan_month_age a ON a.loan_id=l.loan_id AND a.months_on_book=m.mob
          WHERE l.issue_date BETWEEN '2024-11-01' AND '2026-10-31' GROUP BY 1,2""")
        lookup={(r['cohort_month'],r['mob']):r for r in direct}
        for row in rows:
            expected=lookup[row['cohort_month'],row['mob']]
            self.assertEqual(row['original_loan_count'],expected['n'])
            self.assertEqual(row['original_amount'],expected['amount'])
            observed=expected['maturity']<='2026-10-31'
            self.assertEqual(row['observation_status']=='Observed',observed)
            if observed:
                self.assertEqual(row['ever_count'],expected['ever'])
                self.assertAlmostEqual(row['ever_ratio'],expected['ever']/expected['n'])
            else:
                self.assertIsNone(row['ever_ratio'])
                self.assertEqual(row['cell_label'],'—')

    def test_fixed_age_cards_pool_only_mature_cohorts(self):
        k=self.dataset('vintage_kpis')[0]
        matrix=self.dataset('vintage_matrix')
        self.assertEqual(k['original_loans'],8759)
        self.assertEqual(k['cohort_count'],24)
        for mob in [3,6,12]:
            eligible=[r for r in matrix if r['mob']==mob and r['observation_status']=='Observed']
            numerator=sum(r['ever_count'] for r in eligible)
            denominator=sum(r['original_loan_count'] for r in eligible)
            self.assertEqual(k['mob'+str(mob)+'_loans'],denominator)
            self.assertEqual(k['mob'+str(mob)+'_cohorts'],len(eligible))
            self.assertAlmostEqual(k['mob'+str(mob)+'_ratio'],numerator/denominator)

    def test_curves_are_monotonic_observed_and_bounded(self):
        curves=self.dataset('vintage_curves')
        self.assertEqual(len({r['series'] for r in curves}),4)
        for series in {r['series'] for r in curves}:
            points=[r for r in curves if r['series']==series]
            self.assertEqual([r['mob'] for r in points],list(range(1,len(points)+1)))
            self.assertEqual([r['value'] for r in points],sorted(r['value'] for r in points))
            self.assertTrue(all(0<=r['value']<=100 and r['mob']<=12 for r in points))

    def test_filtered_history_recomputes_maturity_and_has_no_future_data(self):
        params=dict(p_date_key=20250831,p_product_id=2,p_region_id=1,p_channel_id=2)
        rows=self.dataset('vintage_matrix',**params)
        direct=self.fetch("""SELECT date_trunc('month',issue_date)::date c,count(*) n FROM credit.loan
          JOIN credit.branch USING(branch_id) WHERE issue_date BETWEEN '2024-11-01' AND '2025-08-31'
          AND product_id=2 AND region_id=1 AND channel_id=2 GROUP BY 1""")
        counts={r['c']:r['n'] for r in direct}
        self.assertEqual(len(rows),len(counts)*12)
        for row in rows:
            self.assertEqual(row['original_loan_count'],counts[row['cohort_month']])
            if row['observation_status']=='Observed':
                self.assertLessEqual(row['maturity_date'],'2025-08-31')
        self.assertTrue(all(r['ever_ratio'] is None for r in rows if r['cohort_month']=='2025-08-01'))

    def test_original_counts_keep_terminal_contracts(self):
        rows=self.dataset('vintage_matrix')
        direct=self.fetch("""SELECT count(*) n FROM credit.loan l JOIN credit.loan_snapshot s USING(loan_id)
          WHERE l.issue_date>='2024-11-01' AND s.snapshot_date='2026-10-31' AND s.loan_status<>'Active'""")[0]
        self.assertGreater(direct['n'],0)
        self.assertEqual(sum(r['original_loan_count'] for r in rows if r['mob']==1),8759)

    def test_empty_and_early_scopes_do_not_invent_zero_rates(self):
        k=self.dataset('vintage_kpis',p_region_id=999)[0]
        self.assertEqual(k['original_loans'],0)
        self.assertIsNone(k['mob3_ratio'])
        self.assertEqual(k['mob3_label'],'—')
        self.assertEqual(self.dataset('vintage_matrix',p_region_id=999),[])
        self.assertEqual(self.dataset('vintage_curves',p_region_id=999),[])
        early=self.dataset('vintage_kpis',p_date_key=20241130)[0]
        self.assertIsNone(early['mob3_ratio'])
        self.assertEqual(self.dataset('vintage_curves',p_date_key=20241130),[])

    def test_reject_unknown_or_noninteger_parameters(self):
        for params in [dict(p_date_key='20261031'),dict(p_region_id=-1),dict(p_unknown=2)]:
            with self.assertRaises(ValueError):
                expand('SELECT 1',**params)

    def test_readable_view_bounds_and_age_dictionary(self):
        first=self.dataset('vintage_kpis')[0]
        self.assertEqual((first.get('matrix_page_no'),first.get('matrix_page_count'),first.get('matrix_mob_start')),(1,4,1))
        last=self.dataset('vintage_kpis',p_vintage_page=9999,p_vintage_mob_start=7)[0]
        self.assertEqual((last['matrix_page_no'],last['matrix_next_page'],last['matrix_mob_start']),(4,4,7))
        zero=self.dataset('vintage_kpis',p_vintage_page=0)[0]
        self.assertEqual((zero['matrix_page_no'],zero['matrix_prev_page']),(1,1))
        self.assertEqual(self.dataset('filter_vintage_mob'),[dict(id=1,label='MOB 1–6'),dict(id=7,label='MOB 7–12')])

    def test_view_selection_does_not_change_measures_or_matrix(self):
        original=self.dataset('vintage_kpis')[0]
        changed=self.dataset('vintage_kpis',p_vintage_page=3,p_vintage_mob_start=7)[0]
        for key in ['original_loans','original_amount','cohort_count','mob3_ratio','mob6_ratio','mob12_ratio']:
            self.assertEqual(original[key],changed[key])
        self.assertEqual(self.dataset('vintage_matrix'),self.dataset('vintage_matrix',p_vintage_page=4,p_vintage_mob_start=7))
        self.assertEqual(self.dataset('vintage_curves'),self.dataset('vintage_curves',p_vintage_page=4,p_vintage_mob_start=7))

    def test_view_clamps_after_historical_and_empty_filters(self):
        historical=self.dataset('vintage_kpis',p_date_key=20250831,p_vintage_page=4)[0]
        self.assertEqual((historical['cohort_count'],historical['matrix_page_count'],historical['matrix_page_no']),(10,2,2))
        empty=self.dataset('vintage_kpis',p_region_id=999,p_vintage_page=4)[0]
        self.assertEqual((empty['matrix_page_count'],empty['matrix_page_no']),(1,1))
        self.assertEqual(empty['matrix_page_label'],'No cohorts · Page 1 of 1')

    def test_visible_sql_blocks_partition_all_original_cells(self):
        self.assertIn('vintage_matrix_view',build_queries(),'Visible rows must be selected in SQL, without nested native VALUE row expressions')
        original=self.dataset('vintage_matrix')
        seen=[]
        for page in range(1,5):
            for mob in [1,7]:
                block=self.dataset('vintage_matrix_view',p_vintage_page=page,p_vintage_mob_start=mob)
                self.assertEqual(len(block),36)
                self.assertEqual({r['cohort_row'] for r in block},set(range((page-1)*6+1,page*6+1)))
                self.assertEqual({r['mob'] for r in block},set(range(mob,mob+6)))
                seen.extend(block)
        self.assertEqual(sorted(seen,key=lambda r:(r['cohort_row'],r['mob'])),original)
        self.assertEqual(self.dataset('vintage_matrix_view',p_region_id=999),[])
        historical=self.dataset('vintage_matrix_view',p_date_key=20250831,p_vintage_page=4,p_vintage_mob_start=7)
        self.assertEqual(len(historical),24)
        self.assertEqual({r['cohort_row'] for r in historical},{7,8,9,10})


if __name__=='__main__':unittest.main()
