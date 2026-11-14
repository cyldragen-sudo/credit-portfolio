"""Behavior checks against the loaded PostgreSQL fixture, when explicitly connected."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from query_contract import render


class ParameterTests(unittest.TestCase):
    def test_reject_untrusted_parameter_text(self):
        with self.assertRaises(ValueError):
            render('SELECT ${p_loan_id}', dict(p_loan_id='1; SELECT 2'))
        with self.assertRaises(ValueError):
            render("SELECT '${p_as_of}'", dict(p_as_of="2026-10-31'; SELECT 2; --"))

    def test_reject_invalid_reporting_window(self):
        with self.assertRaises(ValueError):
            render('SELECT 1', dict(p_as_of='2027-01-01'))
        with self.assertRaises(ValueError):
            render('SELECT 1', dict(p_start='2026-10-31',p_end='2026-01-01'))


@unittest.skipUnless(os.environ.get('PGDATABASE'), 'Set PGDATABASE to run real database regressions')
class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from verify import ROOT, rows
        cls.root, cls.fetch = ROOT, staticmethod(rows)

    def test_unissued_loan_has_no_historical_schedule(self):
        loan = self.fetch("SELECT loan_id FROM credit.loan WHERE issue_date>'2024-11-01' ORDER BY loan_id LIMIT 1")[0]
        sql = (self.root / 'queries/13_loan_schedule.sql').read_text()
        result = self.fetch(render(sql,dict(p_loan_id=int(loan['loan_id']),p_as_of='2024-11-01',p_end='2024-11-01')))
        self.assertEqual(result, [])

    def test_vintage_keeps_original_cohort_denominators(self):
        from decimal import Decimal
        results = self.fetch(render((self.root / 'queries/10_vintage.sql').read_text()))
        counts = {r['cohort_month']:int(r['n']) for r in self.fetch("""
            SELECT date_trunc('month',issue_date)::date cohort_month,count(*) n FROM credit.loan
            WHERE issue_date>='2024-11-01' GROUP BY 1""")}
        self.assertGreater(len(results),0)
        for row in results:
            self.assertEqual(int(row['original_loan_count']),counts[row['cohort_month']])
            self.assertEqual(Decimal(row['ever_31_plus_ratio']).quantize(Decimal('.00000001')),
                (Decimal(row['ever_31_plus_count'])/Decimal(row['original_loan_count'])).quantize(Decimal('.00000001')))
        self.assertFalse(any(row['cohort_month']=='2026-10-01' for row in results))


if __name__ == '__main__':
    unittest.main()
