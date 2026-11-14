"""Build the scoped UI-audit coverage record from source and runtime evidence."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'validation/desktop-audit'
with zipfile.ZipFile(ROOT/'dashboard/report/Portfolio_Overview.fvs') as z:
 store=json.loads(ET.fromstring(z.read('editor.tpl')).find('DuchampTemplateAttr').get('store'))
revision=hashlib.sha256((ROOT/'dashboard/report/Portfolio_Overview.fvs').read_bytes()).hexdigest()
labels={'source':'Source authority and confidence','value':'SQL/value accuracy','within':'Within-chart agreement','details':'Complete source details','cross':'Cross-artifact consistency','quality':'Data-quality controls','conclusion':'Conclusion support','clarity':'Analytical clarity','visual':'Visual and interaction consistency','useful':'Dashboard usefulness and completeness'}
assess={
 'source':'The 49 numerical components retain the declared synthetic source, valid native bindings and unchanged SQL; portable/private/installed parity verified.',
 'within':'All ten charts retain coherent titles, axes, units, legends and native series bindings. Final desktop renders checked; individual marks were not independently recomputed.',
 'cross':'All twenty directed tab transitions retained shared filters and visible local context; source review verifies explicit forwarding of all eleven parameters.',
 'clarity':'All five page purposes and material definitions remain clear, including sales cohorts versus funded flow, all-channel plans, whole-loan exposure and cohort maturity.',
 'visual':'All35 control paths passed and notice overlap was repaired. Four page units retain a P2 small-table-text caveat at1366x768 (approximately9–11px); FullHD is more comfortable. No clipping or notice/data overlap remains in ten final renders.',
 'useful':'All five requested analytical jobs and their existing major sections remain available in the desktop composition; no requested view was removed.'}
na={
 'value':'This request is a desktop readability/navigation audit, not a new independent raw-ledger reconciliation. All30 refreshed headline labels matched current native SQL in dated UI tests; prior numerical audits are retained.',
 'details':'This native FineVIS report has no interactive SQL/source-inspector surface. Delivered SQL and bindings were inspected separately.',
 'quality':'Underlying fixture completeness/duplicates/freshness were not reprofiled in this UI audit. Source data and SQL were unchanged; the PostgreSQL regression suite passed.',
 'conclusion':'The report presents descriptive measurements, with no causal or prescriptive business conclusions to validate.'}
record=dict(version=1,artifact=dict(identity='CREDIT_PORTFOLIO/Portfolio_Overview.fvs',revision=revision,view='Five desktop pages at1366x768 and1920x1080; all20 directed routes; five Apply buttons; independent paging and loan return'),categories=[dict(id=k,label=v,applicable=k not in na,**({'assessment':assess[k]} if k not in na else {'reason':na[k]})) for k,v in labels.items()],units=[])
def unit(uid,label,kind,categories):
 record['units'].append(dict(id=uid,label=label,kind=kind,revision=revision,categories={k:dict(checks=[dict(id='current',state='passed',evidence=ev,revision=revision)],findings=[]) for k,ev in categories.items()}));return record['units'][-1]
files=['overview','sales','quality','loan-default','vintage']
# Actual story order is Overview/Sales/Quality/Vintage/Loan.
files=['overview','sales','quality','vintage','loan-default']
for i,(story,file) in enumerate(zip(store['stories'],files)):
 evidence=[file+'-1366-after.json',file+'-1366-after.jpg',file+'-1920-after.json',file+'-1920-after.jpg','visual-review-after.md']
 page=unit(f'page-{i+1}',story['name'],'component',{'visual':evidence,'clarity':['visual-review.md','visual-review-after.md'],'useful':[file+'-1920-after.jpg','inventory.json']})
 if i in (0,1,2,4):page['categories']['visual']['findings'].append(dict(id='small-table-text-1366-'+str(i+1),status='open',severity='P2',evidence=[file+'-1366-after.json',file+'-1366-after.jpg'],revision=revision))
 if i in (2,4):page['categories']['visual']['findings'].append(dict(id='trial-notice-overlap-'+str(i+1),status='fixed',checkIds=['current'],beforeEvidence=['quality-1920-notice-overlap.json'] if i==2 else ['loan-1366-before.json','loan-1366-before.jpg']))
 for w in story['widgets']:
  kind=w['type'];name=w['name'];y=w['states']['matrix'][5]
  if name.endswith(' value') and 247<=y<374:
   unit(f"kpi-{i+1}-{w['id']}",name,'component',{'source':['state-review-after.json','inventory.json','apply.json']})
  if kind.startswith('d-chart'):
   unit(f"chart-{i+1}-{w['id']}",name,'component',{'source':['state-review-after.json','visual-review.md'],'within':evidence+['visual-review.md']})
for i,title in [(0,'Regional performance'),(1,'Monthly plan vs actual'),(1,'Channel conversion'),(2,'Monthly transitions'),(2,'Loan registry'),(3,'Vintage matrix'),(4,'Operations'),(4,'Payment schedule'),(4,'Contract attributes')]:
 unit('source-'+title.replace(' ','-'),title,'component',{'source':['state-review-after.json','inventory.json']})
routes=json.loads((E/'routes-after-fix.json').read_text());assert len(routes)==20 and all(r['passed'] for r in routes)
for n,r in enumerate(routes):unit('route-'+str(n),r['from']+' → '+r['to'],'control',{'visual':['routes-after-fix.json'],'cross':['routes-after-fix.json','state-review-after.json']})
applies=json.loads((E/'apply.json').read_text());assert len(applies)==5 and all(r['passed'] for r in applies)
for n,r in enumerate(applies):unit('apply-'+str(n),'Apply on '+r['page'],'control',{'visual':['apply.json']})
pagers=json.loads((E/'pagers.json').read_text());assert len(pagers)==8 and all(r['passed'] for r in pagers)
for n,r in enumerate(pagers):unit('pager-'+str(n),r['action'],'control',{'visual':['pagers.json']})
for name in ['Selected-row loan drill','Back to saved registry']:unit(name.replace(' ','-'),name,'control',{'visual':['drill-return.json']})
(E/'coverage.json').write_text(json.dumps(record,indent=2)+'\n')
print('Scoped coverage units:',len(record['units']))
