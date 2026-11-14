#!/usr/bin/env python3
"""Read-only independent reconciliation. No credentials, private data, or DB writes emitted."""
import datetime,json,subprocess,sys,xml.etree.ElementTree as ET,zipfile,re,calendar,csv,io
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import delinquency,vintage,loan_details
from local_database import environment
env=environment(reader=True)
result={'started_utc':datetime.datetime.utcnow().isoformat(),'checks':[],'scopes':{},'limitations':['No browser used; native wiring checked statically.','No database mutations or complete test suite.']}
def fetch(sql):
    p=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',"SELECT coalesce(json_agg(x),'[]'::json) FROM ("+sql.strip().rstrip(';')+") x"],env=env,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr)
    return json.loads(p.stdout,parse_float=Decimal)
def dataset(mod,name,params):return fetch(mod.expand(mod.build_queries()[name]['query'],**params))
def check(name,actual,expected,context=None):
    def eq(a,b):
        if isinstance(a,(float,Decimal)) and isinstance(b,(float,Decimal)):return abs(Decimal(str(a))-Decimal(str(b)))<Decimal('0.000000001')
        return a==b
    passed=eq(actual,expected)
    result['checks'].append(dict(name=name,passed=passed,context=context,**({} if passed else {'actual':actual,'expected':expected})))
def scope(p):
    return ' AND '.join(f'{field}={p[key]}' for key,field in [('p_product_id','l.product_id'),('p_region_id','b.region_id'),('p_channel_id','l.channel_id')] if p.get(key,0)) or 'true'
scopes={'default':{},'historical':dict(p_date_key=20250831,p_product_id=1,p_region_id=1,p_channel_id=2),'empty':dict(p_region_id=999),'early':dict(p_date_key=20241130)}
for label,p in scopes.items():
    date=str(p.get('p_date_key',20261031)); d=f'{date[:4]}-{date[4:6]}-{date[6:]}'
    q=dataset(delinquency,'quality_kpis',p)[0]
    raw=fetch(f"""SELECT coalesce(sum(s.principal_balance),0) portfolio_balance,coalesce(sum(s.overdue_principal),0) overdue_principal,
      coalesce(sum(s.overdue_interest),0) overdue_interest,coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=31),0) exposure_31_plus,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=91),0) exposure_91_plus,count(*) FILTER(WHERE s.principal_balance>0) active_loans,
      count(*) FILTER(WHERE s.principal_balance>0 AND s.dpd>0) past_due_loans
      FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) WHERE s.snapshot_date='{d}' AND {scope(p)}""")[0]
    raw['monthly_writeoffs']=fetch(f"SELECT coalesce(sum(o.principal_amount),0) n FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) WHERE operation_type='WRITE_OFF' AND operation_date BETWEEN date_trunc('month','{d}'::date)::date AND '{d}' AND {scope(p)}")[0]['n']
    for field in raw:check('quality_'+field,q[field],raw[field],label)
    for n in [31,91]:check(f'quality_ratio{n}',q[f'dpd_{n}_plus_ratio'],raw[f'exposure_{n}_plus']/raw['portfolio_balance'] if raw['portfolio_balance'] else None,label)
    obligations=fetch(f"""WITH eligible AS (SELECT l.loan_id FROM credit.loan l JOIN credit.branch b USING(branch_id) WHERE l.issue_date<='{d}' AND {scope(p)}),
      balances AS (SELECT o.loan_id,sum(CASE WHEN operation_type='DISBURSEMENT' THEN principal_amount ELSE -principal_amount END) balance FROM credit.loan_operation o JOIN eligible USING(loan_id) WHERE operation_date<='{d}' GROUP BY 1),
      allocations AS (SELECT a.loan_id,a.schedule_version,a.installment_no,
        coalesce(sum(allocated_amount) FILTER(WHERE component='Principal'),0) principal,
        coalesce(sum(allocated_amount) FILTER(WHERE component='Interest'),0) interest
        FROM credit.payment_allocation a JOIN eligible USING(loan_id) JOIN credit.loan_operation o USING(operation_id) WHERE operation_date<='{d}' GROUP BY 1,2,3),
      arrears AS (SELECT s.loan_id,sum(s.principal_due-coalesce(a.principal,0)) overdue_principal,
        sum(s.interest_due-coalesce(a.interest,0)) overdue_interest,
        min(s.due_date) FILTER(WHERE s.principal_due-coalesce(a.principal,0)+s.interest_due-coalesce(a.interest,0)>0) first_unpaid
        FROM credit.payment_schedule s JOIN eligible USING(loan_id) LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
        WHERE s.effective_from<='{d}' AND s.due_date<'{d}' AND (s.cancelled_on IS NULL OR s.cancelled_on>'{d}') GROUP BY 1),
      reconstructed AS (SELECT e.loan_id,coalesce(z.balance,0) balance,coalesce(a.overdue_principal,0) overdue_principal,coalesce(a.overdue_interest,0) overdue_interest,coalesce('{d}'::date-a.first_unpaid,0) dpd FROM eligible e LEFT JOIN balances z USING(loan_id) LEFT JOIN arrears a USING(loan_id))
      SELECT coalesce(sum(balance),0) portfolio_balance,coalesce(sum(overdue_principal),0) overdue_principal,coalesce(sum(overdue_interest),0) overdue_interest,
      coalesce(sum(balance) FILTER(WHERE dpd>=31),0) exposure_31_plus,coalesce(sum(balance) FILTER(WHERE dpd>=91),0) exposure_91_plus,
      count(*) FILTER(WHERE balance>0) active_loans,count(*) FILTER(WHERE balance>0 AND dpd>0) past_due_loans FROM reconstructed""")[0]
    for field in obligations:check('quality_raw_ledger_obligations_'+field,q[field],obligations[field],label)
    transitions=dataset(delinquency,'quality_transitions',p)
    direct=fetch(f"""SELECT CASE WHEN a.loan_status='Active' THEN CASE WHEN a.dpd=0 THEN '0' WHEN a.dpd<=30 THEN '1-30' WHEN a.dpd<=60 THEN '31-60' WHEN a.dpd<=90 THEN '61-90' ELSE '91+' END ELSE a.loan_status END f,
      CASE WHEN z.loan_status='Active' THEN CASE WHEN z.dpd=0 THEN '0' WHEN z.dpd<=30 THEN '1-30' WHEN z.dpd<=60 THEN '31-60' WHEN z.dpd<=90 THEN '61-90' ELSE '91+' END ELSE z.loan_status END t,count(*) n
      FROM credit.loan_snapshot a JOIN credit.loan_snapshot z USING(loan_id) JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
      WHERE a.snapshot_date=(date_trunc('month','{d}'::date)-interval '1 day')::date AND z.snapshot_date='{d}' AND {scope(p)} GROUP BY 1,2""")
    opening={};moves={}
    for r in direct:opening[r['f']]=opening.get(r['f'],0)+r['n'];moves[r['f'],r['t']]=r['n']
    check('transition_cell_count',len(transitions),49,label)
    for r in transitions:
        key=(r['from_bucket'],r['to_bucket']);check('transition_count',r['loan_count'],moves.get(key,0),[label,*key]);check('transition_opening',r['opening_loans'],opening.get(key[0],0),[label,*key]);check('transition_ratio',r['transition_ratio'],Decimal(moves.get(key,0))/opening[key[0]] if opening.get(key[0]) else None,[label,*key])
    original_open=fetch(f"SELECT count(*) n FROM credit.loan_snapshot a JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) WHERE a.snapshot_date=(date_trunc('month','{d}'::date)-interval '1 day')::date AND {scope(p)}")[0]['n']
    check('transition_retains_all_opening_contracts',sum(r['loan_count'] for r in transitions),original_open,label)
    buckets=dataset(delinquency,'quality_buckets',p)
    check('bucket_balance_reconcile',sum((r['value'] for r in buckets),Decimal(0))*10**9,raw['portfolio_balance'],label)
    check('bucket_count_reconcile',sum(r['active_loans'] for r in buckets),raw['active_loans'],label)
    if label in ['default','historical','empty']:
      for threshold in [0,1,31,91]:
        qp=dict(p,p_min_dpd=threshold);summary=dataset(delinquency,'quality_kpis',qp)[0]
        ids=fetch(f"SELECT s.loan_id FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) WHERE snapshot_date='{d}' AND principal_balance>0 AND loan_status='Active' AND dpd>={threshold} AND {scope(p)} ORDER BY dpd DESC,principal_balance DESC,loan_id")
        count=len(ids);pages=max(1,(count+7)//8)
        check('registry_threshold_total',summary['registry_total'],count,[label,threshold]);check('registry_page_count',summary['registry_page_count'],pages,[label,threshold])
        for field in ['overdue_principal','overdue_interest','dpd_31_plus_ratio','dpd_91_plus_ratio','past_due_loans','monthly_writeoffs']:check('registry_threshold_does_not_change_KPI',summary[field],q[field],[label,threshold,field])
        for page in [0,2,999999]:
          selected=min(max(page,1),pages);rows=dataset(delinquency,'quality_registry',dict(qp,p_quality_page=page))
          check('registry_order_and_page_clamping',[r['loan_id'] for r in rows],[r['loan_id'] for r in ids[(selected-1)*8:selected*8]],[label,threshold,page])
    # Compute ever-31+ from payment obligations at their own due+31 date, not from stored vintage flags.
    independent=fetch(f"""WITH eligible AS (SELECT l.*,date_trunc('month',issue_date)::date cohort FROM credit.loan l JOIN credit.branch b USING(branch_id)
      WHERE issue_date BETWEEN '2024-11-01' AND '{d}' AND {scope(p)}),
      first31 AS (SELECT s.loan_id,min(s.due_date+31) first31 FROM credit.payment_schedule s JOIN eligible l USING(loan_id)
      WHERE (s.cancelled_on IS NULL OR s.cancelled_on>s.due_date+31) AND s.due_date+31<='{d}'
      AND s.principal_due+s.interest_due>(SELECT coalesce(sum(a.allocated_amount),0) FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
      WHERE a.loan_id=s.loan_id AND a.schedule_version=s.schedule_version AND a.installment_no=s.installment_no AND o.operation_date<=s.due_date+31) GROUP BY s.loan_id)
      SELECT l.cohort,m.mob,count(*) n,sum(l.original_principal) amount,max((l.issue_date+make_interval(months=>m.mob))::date) maturity,
      count(*) FILTER(WHERE f.first31<=(l.issue_date+make_interval(months=>m.mob))::date) ever
      FROM eligible l CROSS JOIN generate_series(1,12) m(mob) LEFT JOIN first31 f USING(loan_id) GROUP BY 1,2 ORDER BY 1,2""")
    matrix=dataset(vintage,'vintage_matrix',p);lookup={(r['cohort'],r['mob']):r for r in independent}
    check('vintage_matrix_size',len(matrix),len(independent),label)
    for r in matrix:
        e=lookup[r['cohort_month'],r['mob']];context=[label,r['cohort_month'],r['mob']];mature=e['maturity']<=d
        for a,b in [('original_loan_count','n'),('original_amount','amount'),('maturity_date','maturity')]:check('vintage_'+a,r[a],e[b],context)
        check('vintage_status',r['observation_status'],'Observed' if mature else 'Immature',context)
        check('vintage_ledger_ever',r['ever_count'],e['ever'] if mature else None,context)
        check('vintage_ledger_ratio',r['ever_ratio'],Decimal(e['ever'])/e['n'] if mature else None,context)
    v=dataset(vintage,'vintage_kpis',p)[0]
    check('vintage_original_loans',v['original_loans'],sum(r['n'] for r in independent if r['mob']==1),label)
    check('vintage_original_amount',v['original_amount'],sum((r['amount'] for r in independent if r['mob']==1),Decimal(0)),label)
    check('vintage_cohort_count',v['cohort_count'],len({r['cohort'] for r in independent}),label)
    for mob in [3,6,12]:
        mature=[r for r in independent if r['mob']==mob and r['maturity']<=d];n=sum(r['n'] for r in mature);ever=sum(r['ever'] for r in mature)
        check('vintage_pooled_MOB'+str(mob),v[f'mob{mob}_ratio'],Decimal(ever)/n if n else None,label)
        check('vintage_pooled_denominator'+str(mob),v[f'mob{mob}_loans'],n,label)
    result['scopes'][label]={'params':p,'date':d,'quality':{k:q[k] for k in ['overdue_principal','overdue_interest','dpd_31_plus_ratio','dpd_91_plus_ratio','past_due_loans','monthly_writeoffs']},'transition_opening':opening,'vintage':{k:v[k] for k in ['original_loans','original_amount','cohort_count','mob3_ratio','mob6_ratio','mob12_ratio']}}
    print(label+' quality+vintage complete',flush=True)

for loan in [2170,954,2,38,0,999999]:
  detail_scopes={label:scopes[label] for label in ['default','historical','empty']}
  if loan==2:detail_scopes.update(pre_close=dict(p_date_key=20250630),post_close=dict(p_date_key=20250731))
  if loan==38:detail_scopes.update(pre_writeoff=dict(p_date_key=20260731),post_writeoff=dict(p_date_key=20260831))
  for label,dp in detail_scopes.items():
    p=dict(dp,p_loan_id=loan);date=str(p.get('p_date_key',20261031));d=f'{date[:4]}-{date[4:6]}-{date[6:]}'
    k=dataset(loan_details,'loan_kpis',p)[0]
    raw=fetch(f"""SELECT s.*,CASE WHEN l.actual_close_date<='{d}' THEN l.actual_close_date END close_date,
      CASE WHEN l.actual_close_date<='{d}' THEN l.close_reason END close_reason,
      (SELECT coalesce(sum(principal_amount+interest_amount),0) FROM credit.loan_operation o WHERE o.loan_id=l.loan_id AND o.operation_date<='{d}' AND o.operation_type IN ('REPAYMENT','PREPAYMENT')) cash,
      (SELECT sum(CASE WHEN operation_type='DISBURSEMENT' THEN principal_amount ELSE -principal_amount END) FROM credit.loan_operation o WHERE o.loan_id=l.loan_id AND operation_date<='{d}') ledger_balance
      FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) WHERE s.loan_id={loan} AND snapshot_date='{d}'""")
    if raw:
      r=raw[0]
      for field in ['principal_balance','overdue_principal','overdue_interest','dpd','loan_status','close_reason']:check('detail_'+field,k[field],r[field],[label,loan])
      check('detail_asof_close',k['actual_close_date'],r['close_date'],[label,loan]);check('detail_cash_no_writeoff',k['cash_received'],r['cash'],[label,loan]);check('detail_ledger_balance',k['principal_balance'],r['ledger_balance'],[label,loan])
    else:check('detail_missing_selection',k['selected_loan_id'],0,[label,loan])
    # Independent entire schedule and allocations; test every page, not just first eight rows.
    expected=fetch(f"""SELECT s.*,
      coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Principal' AND o.operation_type<>'WRITE_OFF' AND o.operation_date<='{d}'),0) principal_paid,
      coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Interest' AND o.operation_type<>'WRITE_OFF' AND o.operation_date<='{d}'),0) interest_paid,
      coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Principal' AND o.operation_type='WRITE_OFF' AND o.operation_date<='{d}'),0) principal_written_off,
      coalesce(sum(a.allocated_amount) FILTER(WHERE a.component='Interest' AND o.operation_type='WRITE_OFF' AND o.operation_date<='{d}'),0) interest_written_off
      FROM credit.payment_schedule s LEFT JOIN credit.payment_allocation a USING(loan_id,schedule_version,installment_no) LEFT JOIN credit.loan_operation o USING(operation_id)
      WHERE s.loan_id={loan} AND effective_from<='{d}' GROUP BY s.loan_id,s.schedule_version,s.installment_no ORDER BY s.installment_no""") if raw else []
    owed=[e for e in expected if e['due_date']<d and (not e['cancelled_on'] or e['cancelled_on']>d)]
    unpaid=[e for e in owed if e['principal_due']-e['principal_paid']-e['principal_written_off']+e['interest_due']-e['interest_paid']-e['interest_written_off']>0]
    if raw:
      check('detail_raw_obligations_overdue_principal',k['overdue_principal'],sum((e['principal_due']-e['principal_paid']-e['principal_written_off'] for e in owed),Decimal(0)),[label,loan])
      check('detail_raw_obligations_overdue_interest',k['overdue_interest'],sum((e['interest_due']-e['interest_paid']-e['interest_written_off'] for e in owed),Decimal(0)),[label,loan])
      check('detail_raw_obligations_oldest_unpaid_DPD',k['dpd'],(datetime.date.fromisoformat(d)-datetime.date.fromisoformat(min(e['due_date'] for e in unpaid))).days if unpaid else 0,[label,loan])
    pages=[]
    for page in range(1,k['schedule_page_count']+1):pages+=dataset(loan_details,'loan_schedule',dict(p,p_schedule_page=page))
    check('detail_schedule_count',len(pages),len(expected),[label,loan])
    for actual,e in zip(pages,expected):
      for f in ['principal_paid','interest_paid','principal_written_off','interest_written_off','due_date','principal_due','interest_due']:check('detail_dated_schedule_'+f,actual[f],e[f],[label,loan,e['installment_no']])
      cancel=e['cancelled_on'] if e['cancelled_on'] and e['cancelled_on']<=d else None
      status='Cancelled' if cancel else 'Settled' if e['principal_paid']+e['principal_written_off']>=e['principal_due'] and e['interest_paid']+e['interest_written_off']>=e['interest_due'] else 'Overdue' if e['due_date']<d else 'Due today' if e['due_date']==d else 'Scheduled'
      check('detail_schedule_status',actual['status_label'],status,[label,loan,e['installment_no']]);check('detail_cancellation_asof',actual['cancelled_on'],cancel,[label,loan,e['installment_no']])
    ops=[]
    for page in range(1,k['operation_page_count']+1):ops+=dataset(loan_details,'loan_operations',dict(p,p_operation_page=page))
    expectedops=fetch(f"SELECT operation_id FROM credit.loan_operation WHERE loan_id={loan} AND operation_date<='{d}' ORDER BY operation_date DESC,operation_id DESC") if raw else []
    check('detail_all_operation_pages',[o['operation_id'] for o in ops],[o['operation_id'] for o in expectedops],[label,loan])
    for name,field,scale in [('loan_balance_chart','principal_balance',10**6),('loan_dpd_chart','dpd',1)]:
      history=dataset(loan_details,name,p)
      expectedhist=fetch(f"SELECT snapshot_date,{field}::numeric/{scale} value FROM credit.loan_snapshot WHERE loan_id={loan} AND snapshot_date BETWEEN '2024-11-01' AND '{d}' AND snapshot_date=(date_trunc('month',snapshot_date)+interval '1 month - 1 day')::date ORDER BY snapshot_date") if raw else []
      check('detail_'+name,[(r['snapshot_date'],r['value']) for r in history],[(r['snapshot_date'],r['value']) for r in expectedhist],[label,loan])
    result['scopes'].setdefault('details',{})[f'{label}:{loan}']={f:k.get(f) for f in ['selected_loan_id','principal_balance','overdue_principal','overdue_interest','dpd','loan_status','cash_received','actual_close_date','operation_count','schedule_count']}
  print('loan '+str(loan)+' complete',flush=True)

# Explicit daily DPD boundary source records, reconstructed independently from obligations.
boundary_rows=fetch("""SELECT DISTINCT ON(dpd) loan_id,snapshot_date,dpd,dpd_bucket FROM credit.loan_snapshot
  WHERE snapshot_date BETWEEN '2026-10-01' AND '2026-10-31' AND principal_balance>0 AND dpd IN (0,1,30,31,60,61,90,91)
  ORDER BY dpd,snapshot_date,loan_id""")
for b in boundary_rows:
  loan,d=b['loan_id'],b['snapshot_date']
  raw=fetch(f"""SELECT min(s.due_date) first_unpaid FROM credit.payment_schedule s
    WHERE s.loan_id={loan} AND s.effective_from<='{d}' AND s.due_date<'{d}' AND (s.cancelled_on IS NULL OR s.cancelled_on>'{d}')
    AND s.principal_due+s.interest_due>(SELECT coalesce(sum(a.allocated_amount),0) FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
    WHERE a.loan_id=s.loan_id AND a.schedule_version=s.schedule_version AND a.installment_no=s.installment_no AND operation_date<='{d}')""")[0]
  dpd=(datetime.date.fromisoformat(d)-datetime.date.fromisoformat(raw['first_unpaid'])).days if raw['first_unpaid'] else 0
  check('daily_boundary_DPD_from_obligations',b['dpd'],dpd,b)
  bucket='0' if dpd==0 else '1-30' if dpd<=30 else '31-60' if dpd<=60 else '61-90' if dpd<=90 else '91+'
  check('daily_boundary_bucket',b['dpd_bucket'],bucket,b)
result['daily_DPD_boundary_examples']=boundary_rows
check('daily_boundary_coverage',sorted(r['dpd'] for r in boundary_rows),[0,1,30,31,60,61,90,91])

# Check true clamped anniversaries with Python calendar independently of PostgreSQL interval arithmetic.
anniversaries=fetch("SELECT l.issue_date,a.months_on_book,a.observation_date FROM credit.loan_month_age a JOIN credit.loan l USING(loan_id) WHERE extract(day from l.issue_date)>=28")
bad=[]
for r in anniversaries:
    d=datetime.date.fromisoformat(r['issue_date']);m=d.year*12+d.month-1+r['months_on_book'];year,month=divmod(m,12);month+=1
    expected=datetime.date(year,month,min(d.day,calendar.monthrange(year,month)[1])).isoformat()
    if expected!=r['observation_date']:bad.append(r)
check('calendar_clamped_anniversaries',bad,[]);result['anniversary_rows_checked']=len(anniversaries)

# Portable native SQL, XML datasets and actual page VALUE column indexes.
meta={r['name']:r['columns'] for r in json.loads((ROOT/'validation/native-datasets.json').read_text())}
xml=ET.parse(ROOT/'dashboard/datasets.xml').getroot();native={t.attrib['name']:t for t in xml.findall('TableData')}
for mod in [delinquency,vintage,loan_details]:
  for name,spec in mod.build_queries().items():
    check('native_saved_SQL_'+name,(ROOT/'dashboard/sql'/f'{name}.sql').read_text().strip().rstrip(';'),spec['query'].strip().rstrip(';'))
    check('native_XML_SQL_'+name,native[name].findtext('Query').strip().rstrip(';'),spec['query'].strip().rstrip(';'))
    expanded=mod.expand(spec['query'])
    actual=subprocess.run([env['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c','COPY (SELECT * FROM ('+expanded+') actual_columns LIMIT 0) TO STDOUT WITH CSV HEADER'],env=env,capture_output=True,text=True,check=True)
    columns=next(csv.reader(io.StringIO(actual.stdout)))
    check('native_metadata_matches_actual_DB_columns_'+name,meta[name],columns)
with zipfile.ZipFile(ROOT/'dashboard/report/Portfolio_Overview.fvs') as z:
  packaged=ET.fromstring(z.read('editor.tpl'));store=json.loads(packaged.find('DuchampTemplateAttr').attrib['store'])
  for name,t in native.items():
    if name.startswith(('quality_','vintage_','loan_')):
      packaged_query=next(n.findtext('Query') for n in packaged.findall('.//TableData') if n.attrib.get('name')==name)
      check('native_packaged_report_query_'+name,packaged_query,t.findtext('Query'))
bindings=[]
def strings(obj):
  if isinstance(obj,str):yield obj
  elif isinstance(obj,dict):
    for v in obj.values():yield from strings(v)
  elif isinstance(obj,list):
    for v in obj:yield from strings(v)
for story in store['stories']:
  if story['name'] in ['Delinquency and Portfolio Quality','Vintage Analysis','Loan Details']:
    for w in story['widgets']:
      for string in strings(w):
       for match in re.finditer(r'VALUE\("([^"]+)",(\d+),(\d+)\)',string):
        ds,col,row=match.groups();check('native_binding_column_valid',int(col)<=len(meta.get(ds,[])),True,[story['name'],w['name'],ds,col])
        bindings.append([story['name'],w['name'],ds,int(col),int(row)])
cards={'Delinquency and Portfolio Quality':('quality_kpis','Quality',[('OVERDUE PRINCIPAL','overdue_principal_label'),('OVERDUE INTEREST','overdue_interest_label'),('31+ DPD EXPOSURE','ratio31_label'),('91+ DPD EXPOSURE','ratio91_label'),('PAST-DUE LOANS','past_due_loans_label'),('MONTHLY WRITE-OFFS','writeoff_label')]),
       'Vintage Analysis':('vintage_kpis','Vintage',[('ORIGINAL LOANS','original_loans_label'),('ORIGINAL FUNDED AMOUNT','original_amount_label'),('ORIGINATION COHORTS','cohort_count_label'),('EVER 31+ · MOB 3','mob3_label'),('EVER 31+ · MOB 6','mob6_label'),('EVER 31+ · MOB 12','mob12_label')]),
       'Loan Details':('loan_kpis','Loan',[('PRINCIPAL BALANCE','balance_label'),('OVERDUE PRINCIPAL','overdue_principal_label'),('OVERDUE INTEREST','overdue_interest_label'),('DAYS PAST DUE','dpd_label'),('CONTRACT STATUS','status_label'),('CASH RECEIVED','cash_label')])}
for story in store['stories']:
  if story['name'] in cards:
    ds,prefix,fields=cards[story['name']];widgets={w['name']:w for w in story['widgets']}
    for title,col in fields:
      name=prefix+' '+title+' value';actual=widgets[name]['props']['value'];expected=f'=VALUE("{ds}",{meta[ds].index(col)+1},1)'
      check('native_headline_exact_binding',actual,expected,[story['name'],name,col])
result['native_bindings_checked']=len(bindings)
result['finished_utc']=datetime.datetime.utcnow().isoformat();result['passed']=all(c['passed'] for c in result['checks']);result['check_count']=len(result['checks'])
out=ROOT/'validation/full-audit/quality-vintage-details.json';out.write_text(json.dumps(result,indent=2,default=str)+'\n')
print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'failures':[c for c in result['checks'] if not c['passed']],'evidence':str(out)},default=str))
