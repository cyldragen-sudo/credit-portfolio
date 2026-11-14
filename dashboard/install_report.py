#!/usr/bin/env python3
"""Install the five-page credit report, retaining a private backup before replacement."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def install(webroot,replace=False):
    webroot=Path(webroot).resolve()
    reportlets=webroot/'WEB-INF/reportlets'
    if not reportlets.is_dir():
        raise ValueError('Expected a FineReport webroot containing WEB-INF/reportlets')
    folder=reportlets/'CREDIT_PORTFOLIO'
    target=folder/'Portfolio_Overview.fvs'
    if folder.is_symlink() or target.is_symlink():
        raise ValueError('Refusing symlinked report targets')
    source=ROOT/'.private/Portfolio_Overview.fvs'
    if not source.is_file():
        raise FileNotFoundError('Build the private local report first')
    if target.exists():
        if not replace:
            raise FileExistsError('Credit overview already exists; use --replace to back it up and update')
        backup=ROOT/'.private/report-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup.mkdir(parents=True,mode=0o700)
        shutil.copy2(target,backup/target.name)
    folder.mkdir(exist_ok=True)
    temporary=folder/'Portfolio_Overview.pending'
    shutil.copyfile(source,temporary)
    temporary.chmod(0o600)
    temporary.replace(target)
    (ROOT/'validation/report-installation.json').write_text(json.dumps(dict(
        report='CREDIT_PORTFOLIO/Portfolio_Overview.fvs',
        pages=['Portfolio Overview','Sales and Funnel','Delinquency and Portfolio Quality','Vintage Analysis','Loan Details'],
        local_read_only_connection=True,credentials_in_portable_report=False),indent=2)+'\n')
    print('Installed CREDIT_PORTFOLIO/Portfolio_Overview.fvs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--webroot',type=Path,default=Path('/Applications/FineReport/webapps/webroot'))
    parser.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    install(args.webroot,args.replace)
