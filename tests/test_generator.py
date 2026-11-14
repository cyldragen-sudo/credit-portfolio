import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GeneratorTests(unittest.TestCase):
    def test_fixture_is_reproducible_and_refuses_overwrite(self):
        self.assertTrue((ROOT / 'src/generate.py').exists(), 'Generator has not been implemented')
        with tempfile.TemporaryDirectory() as temp:
            destinations = [Path(temp) / 'one', Path(temp) / 'two']
            for dest in destinations:
                subprocess.run([sys.executable, str(ROOT / 'src/generate.py'), '--loans', '30',
                                '--seed', '42', '--output', str(dest)], check=True, capture_output=True)
            a, b = [p / '002_demo_data.sql.gz' for p in destinations]
            self.assertEqual(a.read_bytes(), b.read_bytes())
            text = gzip.decompress(a.read_bytes()).decode()
            self.assertIn('COPY credit.loan_snapshot', text)
            self.assertNotIn('2026-11-', text.split('COPY credit.loan_snapshot')[1].split('\\.')[0])
            manifest = json.loads((destinations[0] / 'manifest.json').read_text())
            self.assertEqual(manifest['rows']['loan'], 30)
            self.assertGreater(manifest['rows']['payment_allocation'], 0)
            retry = subprocess.run([sys.executable, str(ROOT / 'src/generate.py'), '--output',
                                    str(destinations[0])], capture_output=True)
            self.assertNotEqual(retry.returncode, 0)


if __name__ == '__main__':
    unittest.main()
