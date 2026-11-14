import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_archive_excludes_private_data_and_build_products(self):
        module_file=ROOT/'src/package.py'
        self.assertTrue(module_file.exists(),'Release packager is not implemented')
        spec=importlib.util.spec_from_file_location('credit_packager',module_file)
        package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'project';root.mkdir()
            for name,contents in [('README.md','Public guide'),('.private/reader.pgpass','do-not-publish'),
                                  ('dashboard/build/secret.txt','do-not-publish'),
                                  ('docs/.private/secret.txt','do-not-publish'),
                                  ('dashboard/report/readme.md','Public template notes')]:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(contents)
            output=Path(temp)/'release.zip';package.create_zip(root,output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()),{'credit-portfolio/README.md','credit-portfolio/dashboard/report/readme.md'})
                self.assertTrue(all(b'do-not-publish' not in archive.read(name) for name in archive.namelist()))


if __name__=='__main__':
    unittest.main()
