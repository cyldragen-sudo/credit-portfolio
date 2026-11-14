"""Capture safe installed SQL and UI bindings for repeatable audit comparisons."""
import json,zipfile,xml.etree.ElementTree as E,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from local_database import environment

def main():
 out=ROOT/'validation/full-audit'
 installed=Path('/Applications/FineReport/webapps/webroot/WEB-INF/reportlets/CREDIT_PORTFOLIO/Portfolio_Overview.fvs')
 with zipfile.ZipFile(installed) as z:
  doc=E.fromstring(z.read('editor.tpl'));store=json.loads(doc.find('DuchampTemplateAttr').get('store'))
  defaults={p.find('Attributes').get('name'):int(p.findtext('O')) for p in doc.findall('Parameters/Parameter')}
  definitions={td.get('name'):td.findtext('Query').strip().rstrip(';') for td in doc.findall('TableDataMap/TableData')}
  for item in json.loads((ROOT/'dashboard/datasets.json').read_text()):
   assert definitions[item['name']]==(ROOT/item['file']).read_text().strip().rstrip(';'),item['name']
  metadata={d['name']:d['columns'] for d in json.loads((ROOT/'validation/native-datasets.json').read_text())}
  ui={}
  for n,story in enumerate(store['stories'],1):
   ui[str(n)]={'title':story['name'],'cards':[],'charts':[]}
   for w in story['widgets']:
    formula=w.get('props',{}).get('value','')
    if w['name'].endswith(' value') and isinstance(formula,str) and formula.startswith('=VALUE('):
     match=re.match(r'=VALUE\("([^\"]+)\",(\d+),(\d+)\)',formula)
     if match:ui[str(n)]['cards'].append(dict(widget=w['name'],dataset=match[1],column=metadata[match[1]][int(match[2])-1],row=int(match[3])))
    if w['type'].startswith('d-chart'):
     resource=store['resources'][w['props']['configFile']]['name'].lstrip('/')
     config=E.fromstring(z.read(resource));definition=config.find('.//ChartDefinition/OneValueCDDefinition')
     ui[str(n)]['charts'].append(dict(name=w['name'],dataset=definition.findtext('TableData/Name'),value=definition.get('valueName'),series=definition.get('seriesName'),category=definition.find('CategoryName').get('value')))
  scopes={'default':dict(defaults,p_loan_id=2170),'filtered':dict(defaults,p_date_key=20250831,p_product_id=1,p_region_id=1,p_channel_id=2,p_quality_page=2,p_loan_id=954,p_operation_page=2,p_schedule_page=2),'empty':dict(defaults,p_region_id=999,p_loan_id=999999)}
  statements=[]
  for scope,params in scopes.items():
   for name,sql in definitions.items():
    expanded=re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(params[m[1]]),sql)
    assert '${' not in expanded
    statements.append("SELECT json_build_object('scope','"+scope+"','dataset','"+name+"','rows',coalesce((SELECT json_agg(r) FROM ("+expanded+") r),'[]'::json))::jsonb;")
  env=environment(reader=True)
  run=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1'],input='\n'.join(statements),env=env,capture_output=True,text=True,check=True)
  results={name:{} for name in scopes}
  for line in run.stdout.splitlines():
   row=json.loads(line);results[row['scope']][row['dataset']]=row['rows']
  (out/'native-results.json').write_text(json.dumps(results,indent=2)+'\n')
  (out/'ui-bindings.json').write_text(json.dumps(ui,indent=2)+'\n')
  print('Installed SQL matches source; executed',len(statements),'dataset/scope combinations.')
  for page,info in ui.items():print(page,info['title'],len(info['cards']),'KPI bindings;',len(info['charts']),'charts')

if __name__=='__main__':main()
