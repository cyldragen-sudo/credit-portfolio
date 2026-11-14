#!/usr/bin/env python3
"""Independent, read-only Overview/Sales evidence; no secrets are serialized.
Uses native dataset SQL for actuals, independently written raw-table SQL for expectations.
Run with python3 validation/full-audit/overview-sales.py from this repository.
"""
import datetime, decimal, json, re, subprocess, sys, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from local_database import environment
from overview import build_queries as overview_queries
from sales import build_queries as sales_queries
from delinquency import build_queries as quality_queries
ENV=environment(reader=True)
D=decimal.Decimal
checks=[]

def fetch(q):
    result=subprocess.run([ENV['PSQL'],'-X','-w','-Atq','-v','ON_ERROR_STOP=1','-c',
      "SELECT coalesce(json_agg(t),'[]'::json) FROM ("+q.strip().rstrip(';')+") t"],
      env=ENV,capture_output=True,text=True)
    if result.returncode: raise RuntimeError(result.stderr)
    return json.loads(result.stdout,parse_float=D)

def equivalent(a,b):
    if isinstance(a,(int,D)) and isinstance(b,(int,D)): return abs(D(a)-D(b))<=D('0.000000000001')
    if isinstance(a,dict) and isinstance(b,dict): return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list): return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    return a==b

def check(name,a,b):
    checks.append(dict(check=name,passed=equivalent(a,b),actual=a,expected=b))

def native(name,p):
    q=(ROOT/'dashboard/sql'/f'{name}.sql').read_text()
    return fetch(re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(p.get(m[1],1)),q))

def project(rows,keys): return [{k:r[k] for k in keys} for r in rows]

scenarios=[dict(name='default',date='2026-10-31',p_date_key=20261031,p_product_id=0,p_region_id=0,p_channel_id=0),
 dict(name='historical_personal_moscow_online',date='2025-08-31',p_date_key=20250831,p_product_id=1,p_region_id=1,p_channel_id=2),
 dict(name='empty_region',date='2026-10-31',p_date_key=20261031,p_product_id=0,p_region_id=999,p_channel_id=0)]
report=dict(run_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='Native disk datasets versus independent raw-table sums and dated application events; read-only reporting role.',scenarios=[],checks=checks)
check('read_only_role',fetch("SELECT current_user AS role,current_setting('transaction_read_only') AS read_only"),[dict(role='credit_report_user',read_only='on')])
check('historical_filter_labels',fetch("SELECT (SELECT product_name FROM credit.product WHERE product_id=1) product,(SELECT region_name FROM credit.region WHERE region_id=1) region,(SELECT channel_name FROM credit.channel WHERE channel_id=2) channel"),[dict(product='Personal Loan',region='Moscow',channel='Online')])
for name,spec in {**overview_queries(),**sales_queries()}.items():
    check('generated_sql_matches_source:'+name,(ROOT/'dashboard/sql'/f'{name}.sql').read_text().strip().rstrip(';'),spec['query'].strip().rstrip(';'))
for p in scenarios:
    name=p['name']; date=p['date']; prev="(date_trunc('month',date '"+date+"')-interval '1 day')::date"
    start="date_trunc('month',date '"+date+"')::date"
    def scope(a='l',channel=True):
        terms=[f"({p['p_product_id']}=0 OR {a}.product_id={p['p_product_id']})",f"({p['p_region_id']}=0 OR b.region_id={p['p_region_id']})"]
        if channel: terms.append(f"({p['p_channel_id']}=0 OR {a}.channel_id={p['p_channel_id']})")
        return ' AND '.join(terms)
    joins=' FROM credit.loan_snapshot s JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) '
    sc=scope()
    rawstock=fetch(f"""WITH c AS (SELECT coalesce(sum(s.principal_balance),0) portfolio_balance,
      count(*) FILTER(WHERE s.principal_balance>0) active_loans,count(DISTINCT l.customer_id) FILTER(WHERE s.principal_balance>0) active_borrowers,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=31),0) exposure_31_plus,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=91),0) exposure_91_plus,
      coalesce(sum(s.overdue_principal),0) overdue_principal,coalesce(sum(s.overdue_interest),0) overdue_interest
      {joins} WHERE s.snapshot_date=date '{date}' AND {sc}),
      p AS (SELECT coalesce(sum(s.principal_balance),0) previous_balance {joins} WHERE s.snapshot_date={prev} AND {sc})
      SELECT c.*,p.previous_balance,c.portfolio_balance-p.previous_balance balance_change,
      (c.portfolio_balance-p.previous_balance)/nullif(p.previous_balance,0) balance_change_ratio,
      c.exposure_31_plus/nullif(c.portfolio_balance,0) dpd_31_plus_ratio,c.exposure_91_plus/nullif(c.portfolio_balance,0) dpd_91_plus_ratio FROM c CROSS JOIN p""")[0]
    ov=native('overview_kpis',p)[0]; sales=native('sales_kpis',p)[0]
    check(name+':all_overview_kpis',project([ov],rawstock.keys()),[rawstock])
    flow=fetch(f"""SELECT count(*) funded_loans,coalesce(sum(o.principal_amount),0) funded_amount,avg(o.principal_amount) average_funded_amount,
      sum(o.principal_amount*l.annual_rate)/nullif(sum(o.principal_amount),0) weighted_annual_percent_rate
      FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
      WHERE o.operation_type='DISBURSEMENT' AND o.operation_date BETWEEN {start} AND date '{date}' AND {sc}""")[0]
    check(name+':sales_flow_from_disbursement_ledger',project([sales],['funded_loans','funded_amount','average_funded_amount']),project([flow],['funded_loans','funded_amount','average_funded_amount']))
    check(name+':overview_sales_same_funding',ov['month_to_date_disbursements'],sales['funded_amount'])
    ledger=fetch(f"""SELECT coalesce(sum(CASE WHEN o.operation_type='DISBURSEMENT' THEN o.principal_amount ELSE -o.principal_amount END),0) balance
      FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
      WHERE o.operation_date<=date '{date}' AND {sc}""")[0]['balance']
    check(name+':snapshot_balance_against_independent_ledger',ov['portfolio_balance'],ledger)
    evbase=f"""WITH event_dates AS (SELECT application_id,
      min(event_date) FILTER(WHERE event_status='Approved') approved,
      min(event_date) FILTER(WHERE event_status='Funded') funded,
      min(event_date) FILTER(WHERE event_status='Declined') declined,
      min(event_date) FILTER(WHERE event_status='Withdrawn') withdrawn
      FROM credit.application_event WHERE event_date<=date '{date}' GROUP BY application_id),cohort AS (
      SELECT a.*,e.approved,e.funded,e.declined,e.withdrawn FROM credit.application a JOIN credit.branch b USING(branch_id)
      LEFT JOIN event_dates e USING(application_id) WHERE a.submitted_date BETWEEN {start} AND date '{date}' AND {scope('a')})"""
    cohort=fetch(evbase+""" SELECT count(*) submitted_applications,count(approved) approved_applications,
      count(funded) cohort_funded_applications,count(declined) declined_applications,count(withdrawn) withdrawn_applications,
      count(*) FILTER(WHERE funded IS NULL AND declined IS NULL AND withdrawn IS NULL) in_progress_applications,
      avg(funded-submitted_date) average_days_to_funding,count(approved)::numeric/nullif(count(*),0) approval_ratio,
      count(funded)::numeric/nullif(count(approved),0) approved_to_funded_ratio FROM cohort""")[0]
    check(name+':sales_cohort_from_dated_events',project([sales],cohort.keys()),[cohort])
    check(name+':cohort_terminal_partition',sales['submitted_applications'],sum(sales[k] for k in ['cohort_funded_applications','declined_applications','withdrawn_applications','in_progress_applications']))
    expected_funnel=[] if not cohort['submitted_applications'] else [dict(stage=i,label=label,series='Applications',value=cohort[k]) for i,label,k in [(1,'Submitted','submitted_applications'),(2,'Approved','approved_applications'),(3,'Funded','cohort_funded_applications')]]
    check(name+':funnel_all_stages',native('sales_funnel_chart',p),expected_funnel)
    ch=fetch(evbase+""" SELECT c.channel_id,n.channel_name,count(*) submitted_applications,count(approved) approved_applications,count(funded) cohort_funded_applications,
      count(approved)::numeric/nullif(count(*),0) approval_ratio,count(funded)::numeric/nullif(count(approved),0) conversion_ratio,avg(funded-submitted_date) avg_days
      FROM cohort c JOIN credit.channel n USING(channel_id) GROUP BY 1,2 ORDER BY 1""")
    native_ch=native('sales_channel_table',p)
    check(name+':channel_counts',project(native_ch,['channel_id','channel_name','submitted_applications','approved_applications','cohort_funded_applications']),project(ch,['channel_id','channel_name','submitted_applications','approved_applications','cohort_funded_applications']))
    # Native display labels are checked by independently formatting raw-event ratios in PostgreSQL.
    labels=fetch(evbase+""" SELECT c.channel_id,
      coalesce(to_char(count(approved)::numeric/nullif(count(*),0)*100,'FM990.0')||'%','—') approval_label,
      coalesce(to_char(count(funded)::numeric/nullif(count(approved),0)*100,'FM990.0')||'%','—') conversion_label,
      coalesce(to_char(avg(funded-submitted_date),'FM990.0'),'—') days_label FROM cohort c GROUP BY 1 ORDER BY 1""")
    check(name+':channel_display_rates_and_days',project(native_ch,['channel_id','approval_label','conversion_label','days_label']),labels)
    channels=fetch(f"""SELECT c.channel_name label,'Disbursements'::text series,sum(o.principal_amount)/1000000 value FROM credit.loan_operation o
      JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id) JOIN credit.channel c USING(channel_id)
      WHERE o.operation_type='DISBURSEMENT' AND o.operation_date BETWEEN {start} AND date '{date}' AND {sc} GROUP BY c.channel_name ORDER BY value DESC""")
    check(name+':channel_sales_all_bars',native('sales_channel_chart',p),channels)
    plan=fetch(f"""WITH target AS (SELECT p.product_id,sum(p.planned_amount) planned_amount FROM credit.sales_plan p JOIN credit.branch b USING(branch_id)
      WHERE p.plan_month={start} AND {scope('p',False)} GROUP BY 1), actual AS (SELECT l.product_id,count(*) funded_loans,sum(o.principal_amount) funded_amount
      FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
      WHERE o.operation_type='DISBURSEMENT' AND o.operation_date BETWEEN {start} AND date '{date}' AND {scope('l',False)} GROUP BY 1)
      SELECT t.product_id,n.product_name,coalesce(a.funded_loans,0) funded_loans,coalesce(a.funded_amount,0) funded_amount,t.planned_amount,
      coalesce(a.funded_amount,0)/nullif(t.planned_amount,0) plan_attainment FROM target t JOIN credit.product n USING(product_id) LEFT JOIN actual a USING(product_id) ORDER BY 1""")
    native_plan=native('sales_plan_table',p)
    check(name+':plan_all_rows_ledger_actual_weighted_attainment',project(native_plan,['product_id','product_name','funded_loans','funded_amount','planned_amount','plan_attainment']),plan)
    check(name+':plan_intentionally_ignores_channel',native_plan,native('sales_plan_table',dict(p,p_channel_id=0)))
    products=fetch(f"SELECT n.product_name label,'Principal balance'::text series,sum(s.principal_balance)/1000000000 value {joins} JOIN credit.product n USING(product_id) WHERE s.snapshot_date=date '{date}' AND {sc} AND s.principal_balance>0 GROUP BY n.product_name ORDER BY value DESC")
    check(name+':product_composition_all_bars',native('product_chart',p),products)
    regions=fetch(f"""WITH c AS (SELECT b.region_id,r.region_name,sum(s.principal_balance) balance,count(DISTINCT l.customer_id) FILTER(WHERE s.principal_balance>0) borrowers,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=31),0)/nullif(sum(s.principal_balance),0) ratio31,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=91),0)/nullif(sum(s.principal_balance),0) ratio91 {joins} JOIN credit.region r USING(region_id)
      WHERE s.snapshot_date=date '{date}' AND {sc} GROUP BY 1,2), p AS (SELECT b.region_id,sum(s.principal_balance) balance {joins} WHERE s.snapshot_date={prev} AND {sc} GROUP BY 1)
      SELECT c.*,coalesce(CASE WHEN c.balance>=p.balance THEN '+' ELSE '' END||to_char((c.balance-p.balance)/nullif(p.balance,0)*100,'FM990.00')||'%','—') growth_label FROM c LEFT JOIN p USING(region_id) ORDER BY c.balance DESC,c.region_id""")
    check(name+':regional_all_rows_balances_distinct_borrowers_weighted_rates_growth',project(native('region_table',p),['region_id','region_name','balance','borrowers','ratio31','ratio91','growth_label']),regions)
    trend=fetch(f"""SELECT s.snapshot_date,sum(s.principal_balance) portfolio_balance,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=31),0)/nullif(sum(s.principal_balance),0) dpd_31_plus_ratio,
      coalesce(sum(s.principal_balance) FILTER(WHERE s.dpd>=91),0)/nullif(sum(s.principal_balance),0) dpd_91_plus_ratio
      {joins} WHERE s.snapshot_date BETWEEN date '2024-11-01' AND date '{date}' AND s.snapshot_date=(date_trunc('month',s.snapshot_date)+interval '1 month - 1 day')::date AND {sc} GROUP BY 1 ORDER BY 1""")
    check(name+':overview_trend_every_month_all_rates',native('overview_trend',p),trend)
    balances=native('balance_chart',p); qualities=native('quality_chart',p)
    check(name+':balance_chart_values',project(balances,['sort_date','value']),[dict(sort_date=r['snapshot_date'],value=r['portfolio_balance']/D(1000000000)) for r in trend])
    check(name+':quality_chart_values',project(qualities,['sort_date','series','value']),[dict(sort_date=r['snapshot_date'],series=s,value=None if r[k] is None else r[k]*100) for r in trend for s,k in [('31+ DPD','dpd_31_plus_ratio'),('91+ DPD','dpd_91_plus_ratio')]])
    flowtrend=fetch(f"""WITH amounts AS (SELECT date_trunc('month',o.operation_date)::date month_start,sum(o.principal_amount)/1000000 value
      FROM credit.loan_operation o JOIN credit.loan l USING(loan_id) JOIN credit.branch b USING(branch_id)
      WHERE o.operation_type='DISBURSEMENT' AND o.operation_date BETWEEN date '2024-11-01' AND date '{date}' AND {sc} GROUP BY 1)
      SELECT (g+interval '1 month - 1 day')::date month_end,coalesce(a.value,0) value FROM generate_series(date '2024-11-01',{start},interval '1 month') g
      LEFT JOIN amounts a ON a.month_start=g::date WHERE EXISTS(SELECT 1 FROM amounts) ORDER BY 1""")
    check(name+':sales_trend_every_month_from_ledger',project(native('sales_trend_chart',p),['month_end','value']),flowtrend)
    quality=native('quality_kpis',dict(p,p_min_dpd=1,p_quality_page=1))[0]
    stockkeys=['portfolio_balance','active_loans','exposure_31_plus','exposure_91_plus','dpd_31_plus_ratio','dpd_91_plus_ratio','overdue_principal','overdue_interest']
    check(name+':overview_quality_same_stocks',project([ov],stockkeys),project([quality],stockkeys))
    report['scenarios'].append(dict(parameters=p,overview_headlines={k:ov[k] for k in ['portfolio_label','funding_label','borrowers_label','growth_label','ratio_31_label','ratio_91_label']},sales_headlines={k:sales[k] for k in ['funded_amount_label','funded_loans_label','average_amount_label','applications_label','approval_label','conversion_label']},raw_stock=rawstock,raw_flow=flow,raw_event_cohort=cohort,plan=plan,channel_cohort=ch,trend_months=len(trend),overview_scope_note=ov['scope_note'],sales_scope_note=sales['scope_note']))
# Verify the actual distributable artifact rather than inferring correctness from builders.
with zipfile.ZipFile(ROOT/'dashboard/report/Portfolio_Overview.fvs') as archive:
    root=ET.fromstring(archive.read('editor.tpl'))
    store=json.loads(root.find('DuchampTemplateAttr').get('store'))
    relevant=set(overview_queries())|set(sales_queries())
    for data in root.findall('.//TableData'):
        name=data.get('name')
        if name in relevant:
            check('compiled_report_sql:'+name,data.find('Query').text.strip().rstrip(';'),(ROOT/'dashboard/sql'/f'{name}.sql').read_text().strip().rstrip(';'))
    headline_fields=[{
      'PORTFOLIO BALANCE value':'portfolio_label','MTD DISBURSEMENTS value':'funding_label',
      'ACTIVE BORROWERS value':'borrowers_label','MONTHLY GROWTH value':'growth_label',
      '31+ DPD EXPOSURE value':'ratio_31_label','91+ DPD EXPOSURE value':'ratio_91_label'}, {
      'Sales DISBURSEMENTS value':'funded_amount_label','Sales FUNDED LOANS value':'funded_loans_label',
      'Sales AVG FUNDED AMOUNT value':'average_amount_label','Sales APPLICATIONS value':'applications_label',
      'Sales APPROVAL RATE value':'approval_label','Sales APPROVED TO FUNDED value':'conversion_label'}]
    chart_datasets=[{'Portfolio trend':'balance_chart','Delinquency trend':'quality_chart','Product composition':'product_chart'},
      {'Application funnel':'sales_funnel_chart','Disbursement trend':'sales_trend_chart','Sales by channel':'sales_channel_chart'}]
    for i,page in enumerate(store['stories'][:2]):
        dataset=['overview_kpis','sales_kpis'][i]
        actual_columns=list(native(dataset,scenarios[0])[0])
        widgets={w['name']:w for w in page['widgets']}
        for name,column in headline_fields[i].items():
            expected='=VALUE("'+dataset+'",'+str(actual_columns.index(column)+1)+',1)'
            check('compiled_headline_binding:'+name,widgets[name]['props']['value'],expected)
        for name,dataset in chart_datasets[i].items():
            config_id=widgets[name]['props']['configFile']
            resource=store['resources'][config_id]['name'].lstrip('/')
            chart=ET.fromstring(archive.read(resource))
            definition=chart.find('.//ChartDefinition/OneValueCDDefinition')
            check('compiled_chart_dataset:'+name,definition.find('TableData/Name').text,dataset)
            check('compiled_chart_value_column:'+name,definition.get('valueName'),'value')
        for name,parameter in [('As of','p_date_key'),('Product','p_product_id'),('Region','p_region_id'),('Channel','p_channel_id')]:
            check('compiled_filter_parameter:'+page['name']+':'+name,widgets[name+' selector']['props']['relatedParams']['valueConfig'],parameter)
    report['compiled_report']='dashboard/report/Portfolio_Overview.fvs'
report['limits']=['No browser rendering exercised in this bounded read-only sub-audit.',
  'DPD and arrears are aggregated from raw loan_snapshot; principal balances additionally reconcile independently to signed loan_operation cash/debt events.',
  'Original-amount-weighted annual rate is recorded as raw evidence but is not a visible Overview/Sales KPI.']
report['summary']=dict(checks=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks))
output=ROOT/'validation/full-audit/overview-sales.json'
output.write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps(report['summary']))
for c in checks:
    if not c['passed']: print(c['check'],json.dumps(dict(actual=c['actual'],expected=c['expected']),default=str))
