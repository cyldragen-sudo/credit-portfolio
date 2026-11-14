#!/usr/bin/env python3
"""Atomically load an empty credit schema; libpq environment supplies connection details."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def psql(*args, **kwargs):
    if not os.environ.get('PGDATABASE'):
        raise RuntimeError('Set PGDATABASE explicitly to the intended demo database')
    return subprocess.run([os.environ.get('PSQL', 'psql'), '-X', '-w', '-v', 'ON_ERROR_STOP=1', *args],
                          check=True, **kwargs)


def scalar(sql):
    return psql('-Atq', '-c', sql, capture_output=True, text=True).stdout.strip()


def initialize(fixture_directory):
    fixture_directory = Path(fixture_directory)
    manifest = json.loads((fixture_directory / 'manifest.json').read_text())
    fixture = fixture_directory / '002_demo_data.sql.gz'
    digest = hashlib.sha256()
    with fixture.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != manifest['fixture_sha256']:
        raise ValueError('Fixture checksum does not match manifest')
    if int(scalar('SHOW server_version_num')) < 160000:
        raise ValueError('PostgreSQL 16 or newer is required')
    if scalar("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='credit')") != 'f':
        raise ValueError('Refusing initialization: credit schema already exists; use an empty database')
    with tempfile.TemporaryDirectory(prefix='credit-restore-') as temp:
        script = Path(temp) / 'restore.sql'
        with script.open('wb') as target:
            for source in [ROOT / 'database/001_schema.sql', fixture, ROOT / 'database/003_views.sql']:
                opener = gzip.open if source.suffix == '.gz' else open
                with opener(source, 'rb') as stream:
                    shutil.copyfileobj(stream, target)
                target.write(b'\n')
            target.write(b'ANALYZE;\n')
        psql('--single-transaction', '-q', '-f', str(script))
    print('Initialized credit schema, synthetic data, reporting views and English comments.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=ROOT / 'data/generated')
    initialize(parser.parse_args().fixture)
