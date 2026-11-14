#!/usr/bin/env python3
"""Manage this project's private persistent PostgreSQL 16 instance only."""
import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.private'
PG_BIN = Path(os.environ.get('PG_BIN', '/Library/PostgreSQL/16/bin'))
HOST, PORT, DATABASE = '127.0.0.1', 55433, 'credit_portfolio_demo'
MARKER = 'CREDIT_PORTFOLIO_DEMO_20261104'


def private_text(path, value):
    with path.open('w') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(value)


def environment(reader=False):
    env = {k:v for k,v in os.environ.items() if not k.startswith('PG')}
    env.update(PGHOST=HOST, PGPORT=str(PORT), PGDATABASE=DATABASE,
               PGUSER='credit_report_user' if reader else 'credit_admin',
               PGPASSFILE=str(PRIVATE / ('reader.pgpass' if reader else 'admin.pgpass')),
               PGCONNECT_TIMEOUT='8', PSQL=str(PG_BIN / 'psql'))
    return env


def sql(query, database=DATABASE):
    env=environment()
    env['PGDATABASE']=database
    result=subprocess.run([str(PG_BIN/'psql'),'-X','-w','-Atq','-v','ON_ERROR_STOP=1'],
                          input=query,env=env,capture_output=True,text=True,check=True)
    return result.stdout.strip()


def quote(value):
    return "'"+str(value).replace("'","''")+"'"


def verifier(password):
    salt=secrets.token_bytes(16)
    key=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,4096)
    stored=hashlib.sha256(hmac.new(key,b'Client Key',hashlib.sha256).digest()).digest()
    server=hmac.new(key,b'Server Key',hashlib.sha256).digest()
    encode=lambda value:base64.b64encode(value).decode()
    return 'SCRAM-SHA-256$4096:'+encode(salt)+'$'+encode(stored)+':'+encode(server)


def running():
    return subprocess.run([str(PG_BIN/'pg_ctl'),'-D',str(PRIVATE/'pgdata'),'status'],
                          capture_output=True).returncode==0


def start():
    if running():
        print('Project PostgreSQL is already running on 127.0.0.1:55433.')
        return
    options='-h 127.0.0.1 -p 55433 -k '+shlex.quote(str(PRIVATE))
    subprocess.run([str(PG_BIN/'pg_ctl'),'-D',str(PRIVATE/'pgdata'),'-l',str(PRIVATE/'postgres.log'),
                    '-o',options,'-w','start'],check=True)


def initialize():
    PRIVATE.mkdir(exist_ok=True,mode=0o700)
    PRIVATE.chmod(0o700)
    if not (PRIVATE/'pgdata/PG_VERSION').exists():
        # Refuse a port occupied by a different database server.
        probe=subprocess.run([str(PG_BIN/'pg_isready'),'-h',HOST,'-p',str(PORT)],capture_output=True)
        if probe.returncode in (0,1):
            raise RuntimeError('Port 55433 is occupied; no existing instance was modified')
        password=secrets.token_urlsafe(36)
        private_text(PRIVATE/'admin.pgpass',f'{HOST}:{PORT}:*:credit_admin:{password}\n')
        with tempfile.NamedTemporaryFile(mode='w',prefix='credit-init-') as secret_file:
            os.fchmod(secret_file.fileno(),0o600)
            secret_file.write(password+'\n')
            secret_file.flush()
            subprocess.run([str(PG_BIN/'initdb'),'-D',str(PRIVATE/'pgdata'),'-U','credit_admin',
                '--auth-local=scram-sha-256','--auth-host=scram-sha-256','--encoding=UTF8','--locale=C',
                '--pwfile='+secret_file.name],check=True,stdout=subprocess.DEVNULL)
    if not (PRIVATE/'admin.pgpass').exists():
        raise RuntimeError('Existing private cluster has no matching credential file')
    start()
    exists=sql("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname='credit_portfolio_demo')",'postgres')=='t'
    if not exists:
        sql('CREATE DATABASE credit_portfolio_demo','postgres')
        sql('COMMENT ON DATABASE credit_portfolio_demo IS '+quote(MARKER),'postgres')
    elif sql("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname='credit_portfolio_demo'",'postgres')!=MARKER:
        raise RuntimeError('Existing database is not marked as this project; refused')
    if sql("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='credit')")=='f':
        with (PRIVATE/'load.log').open('w') as log:
            subprocess.run([os.sys.executable,str(ROOT/'src/database.py')],env=environment(),check=True,stdout=log,stderr=log)
    else:
        if sql('SELECT seed::text||\':\'||loan_count::text FROM credit.dataset_run')!='20261104:12000':
            raise RuntimeError('Existing credit schema differs from the delivered fixture')
    reader_exists=sql("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='credit_report_user')")=='t'
    if not reader_exists:
        password=secrets.token_urlsafe(36)
        private_text(PRIVATE/'reader.pgpass',f'{HOST}:{PORT}:{DATABASE}:credit_report_user:{password}\n')
        sql('CREATE ROLE credit_report_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '+quote(verifier(password)))
        sql('COMMENT ON ROLE credit_report_user IS '+quote(MARKER))
    elif sql("SELECT shobj_description(oid,'pg_authid') FROM pg_roles WHERE rolname='credit_report_user'")!=MARKER or not (PRIVATE/'reader.pgpass').exists():
        raise RuntimeError('Existing reporting role cannot be safely reused')
    sql("""REVOKE ALL ON DATABASE credit_portfolio_demo FROM PUBLIC;
        GRANT CONNECT ON DATABASE credit_portfolio_demo TO credit_report_user;
        REVOKE CREATE ON SCHEMA public FROM PUBLIC;
        GRANT USAGE ON SCHEMA credit TO credit_report_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA credit TO credit_report_user;
        ALTER ROLE credit_report_user IN DATABASE credit_portfolio_demo SET default_transaction_read_only=on;
        ALTER ROLE credit_report_user IN DATABASE credit_portfolio_demo SET statement_timeout='20s';""")
    result=json.loads(sql("""SELECT json_build_object('host','127.0.0.1','port',55433,
        'database',current_database(),'loans',(SELECT count(*) FROM credit.loan),
        'snapshots',(SELECT count(*) FROM credit.loan_snapshot),
        'reader_can_update',has_table_privilege('credit_report_user','credit.loan','UPDATE'))"""))
    assert result['loans']==12000 and result['snapshots']==5405234 and not result['reader_can_update']
    (ROOT/'validation/local-database.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('init','start','stop','status'))
    command=parser.parse_args().command
    if command=='init':
        initialize()
    elif command=='start':
        start()
    elif command=='stop':
        if running():
            subprocess.run([str(PG_BIN/'pg_ctl'),'-D',str(PRIVATE/'pgdata'),'-m','fast','-w','stop'],check=True)
    else:
        print('Running on 127.0.0.1:55433' if running() else 'Stopped')
