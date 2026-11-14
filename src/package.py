#!/usr/bin/env python3
"""Create an audited portable release, excluding local database and credentials."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TOP={'database','data','queries','src','tests','docs','dashboard','validation','finebi'}
ROOT_FILES={'README.md','.gitignore','compose.yaml'}
EXCLUDED={'.private','build','__pycache__','.git','.superpowers','node_modules'}


def create_zip(root,output,forbidden_values=()):
    root,output=Path(root),Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    files=[]
    for folder,dirs,names in os.walk(root):
        relative=Path(folder).relative_to(root)
        dirs[:]=[name for name in dirs if name not in EXCLUDED and not name.startswith('.')
                 and (relative.parts or name in TOP)]
        for name in names:
            path=Path(folder)/name
            if not relative.parts and name not in ROOT_FILES:continue
            if name.startswith('.') and name!='.gitignore':continue
            if path.suffix in ('.class','.jar','.pyc','.zip') or name=='release-audit.json':continue
            if path.suffix=='.log' and relative.parts[0]!='validation':continue
            if path.is_symlink():raise ValueError('Refusing symlink in release')
            files.append(path)
    temporary=output.with_suffix('.pending')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(files):
            contents=path.read_bytes()
            if any(value and value in contents for value in forbidden_values):
                raise ValueError('Private credential detected; release refused')
            if path.suffix=='.fvs':
                with zipfile.ZipFile(io.BytesIO(contents)) as report:
                    xml=report.read('editor.tpl')
                    if b'JDBCDatabaseConnection' in xml or b'<Password' in xml:
                        raise ValueError('Embedded connection found in portable report')
                    if any(value and value in xml for value in forbidden_values):
                        raise ValueError('Private credential found in report')
            archive.writestr('credit-portfolio/'+str(path.relative_to(root)),contents)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:raise ValueError('Release ZIP integrity failure')
    temporary.replace(output)
    return dict(file_count=len(files),bytes=output.stat().st_size,
                sha256=hashlib.sha256(output.read_bytes()).hexdigest(),private_files_excluded=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT.parents[1]/'outputs/credit-portfolio-complete-2026-11-04.zip')
    args=parser.parse_args()
    secrets=[]
    for name in ('reader.pgpass','admin.pgpass'):
        path=ROOT/'.private'/name
        if path.exists():secrets.append(path.read_text().strip().split(':',4)[-1].encode())
    result=create_zip(ROOT,args.output,secrets)
    (ROOT/'validation/release-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(result,archive=str(args.output)),indent=2))
