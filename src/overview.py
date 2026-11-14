#!/usr/bin/env python3
"""Build the native Portfolio Overview datasets and numeric parameter contract."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
DEFAULTS=dict(p_date_key=20261031,p_product_id=0,p_region_id=0,p_channel_id=0)
AS_OF="""(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)"""


def adapted(sql):
    sql=sql.replace("'${p_as_of}'::date",AS_OF).replace("'${p_start}'::date","'2024-11-01'::date")
    for name in ('p_product_id','p_region_id','p_channel_id'):
        sql=sql.replace('${'+name+'}','${INT('+name+')}')
    return sql.strip().rstrip(';')


def amount_label(expression):
    return "CASE WHEN abs({e})>=1000000000 THEN 'RUB '||to_char({e}/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char({e}/1000000,'FM999,990.00')||' m' END".format(e=expression)


def build_queries():
    kpi=adapted((ROOT/'queries/01_overview_kpis.sql').read_text())
    kpi="""WITH k AS ({base}) SELECT k.*,
    {portfolio} AS portfolio_label,{funding} AS funding_label,
    to_char(active_borrowers,'FM999,999,990') AS borrowers_label,
    to_char(active_loans,'FM999,999,990')||' active loans' AS active_loans_label,
    coalesce(to_char(dpd_31_plus_ratio*100,'FM990.00')||'%','—') AS ratio_31_label,
    coalesce(to_char(dpd_91_plus_ratio*100,'FM990.00')||'%','—') AS ratio_91_label,
    coalesce(CASE WHEN balance_change_ratio>=0 THEN '+' ELSE '' END||to_char(balance_change_ratio*100,'FM990.00')||'%','—') AS growth_label,
    {growth}||' change' AS growth_amount_label,
    {exposure31}||' exposure' AS exposure_31_label,{exposure91}||' exposure' AS exposure_91_label,
    CASE WHEN active_loans=0 THEN 'No loans match the selected filters.' ELSE
    'End-of-day principal balances · Full-loan exposure by days past due' END AS scope_note,
    coalesce(to_char(as_of_date,'DD Mon YYYY'),'No reporting date') AS date_label,
    coalesce(to_char(as_of_date,'FMMonth YYYY'),'No reporting date')||' funding' AS funding_note,
    'vs '||to_char(date_trunc('month',as_of_date)-interval '1 day','DD Mon YYYY') AS comparison_note
    FROM k""".format(base=kpi,portfolio=amount_label('portfolio_balance'),funding=amount_label('month_to_date_disbursements'),
                   growth=amount_label('balance_change'),exposure31=amount_label('exposure_31_plus'),exposure91=amount_label('exposure_91_plus'))
    trend=adapted((ROOT/'queries/02_overview_trend.sql').read_text())
    scope="""(${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
      AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
      AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})"""
    region="""WITH states AS (SELECT * FROM credit.v_snapshot WHERE snapshot_date IN ({asof},
      (date_trunc('month',{asof})-interval '1 day')::date) AND {scope}),
      current_state AS (SELECT region_id,region_name,sum(principal_balance) balance,
        count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) borrowers,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) ratio31,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) ratio91
        FROM states WHERE snapshot_date={asof} GROUP BY 1,2),
      previous_state AS (SELECT region_id,sum(principal_balance) balance FROM states
        WHERE snapshot_date=(date_trunc('month',{asof})-interval '1 day')::date GROUP BY 1)
      SELECT c.region_id,c.region_name,c.balance,c.borrowers,c.ratio31,c.ratio91,
      to_char(c.balance/1000000000,'FM990.00') AS balance_label,
      coalesce(CASE WHEN c.balance>=p.balance THEN '+' ELSE '' END||to_char((c.balance-p.balance)/nullif(p.balance,0)*100,'FM990.00')||'%','—') AS growth_label,
      to_char(c.borrowers,'FM999,990') AS borrowers_label,
      coalesce(to_char(c.ratio31*100,'FM990.00')||'%','—') AS ratio31_label,
      coalesce(to_char(c.ratio91*100,'FM990.00')||'%','—') AS ratio91_label
      FROM current_state c LEFT JOIN previous_state p USING(region_id) ORDER BY c.balance DESC,c.region_id""".format(asof=AS_OF,scope=scope)
    datasets={
        'overview_kpis':kpi,
        'overview_trend':trend,
        'balance_chart':"SELECT snapshot_date AS sort_date,to_char(snapshot_date,'Mon YY') label,'Portfolio'::text series,portfolio_balance/1000000000 AS value FROM ("+trend+") t ORDER BY snapshot_date",
        'quality_chart':"SELECT snapshot_date AS sort_date,to_char(snapshot_date,'Mon YY') label,'31+ DPD'::text series,dpd_31_plus_ratio*100 AS value FROM ("+trend+") t UNION ALL SELECT snapshot_date,to_char(snapshot_date,'Mon YY'),'91+ DPD',dpd_91_plus_ratio*100 FROM ("+trend+") t ORDER BY sort_date,series",
        'product_chart':"SELECT product_name label,'Principal balance'::text series,sum(principal_balance)/1000000000 AS value FROM credit.v_snapshot WHERE snapshot_date="+AS_OF+' AND '+scope+' AND principal_balance>0 GROUP BY product_name ORDER BY value DESC',
        'region_table':region,
        'filter_date':"SELECT to_char(calendar_date,'YYYYMMDD')::integer AS id,to_char(calendar_date,'FMMonth YYYY') label FROM credit.calendar CROSS JOIN credit.dataset_run WHERE calendar_date=month_end AND calendar_date BETWEEN report_start AND as_of_date ORDER BY calendar_date DESC",
        'filter_product':"SELECT 0 id,'All Products' label UNION ALL SELECT product_id,product_name FROM credit.product ORDER BY id",
        'filter_region':"SELECT 0 id,'All Regions' label UNION ALL SELECT region_id,region_name FROM credit.region ORDER BY id",
        'filter_channel':"SELECT 0 id,'All Channels' label UNION ALL SELECT channel_id,channel_name FROM credit.channel ORDER BY id",
    }
    return {name:dict(query=sql,parameters={p:DEFAULTS[p] for p in DEFAULTS if '${INT('+p+')}' in sql}) for name,sql in datasets.items()}


def expand(sql,**overrides):
    params=dict(DEFAULTS,**overrides)
    if any(type(value) is not int or value<0 for value in params.values()) or set(params)!=set(DEFAULTS):
        raise ValueError('Only known nonnegative integer parameters are allowed')
    return re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(params[m.group(1)]),sql)


if __name__=='__main__':
    from sales import build_queries as sales_queries
    from delinquency import build_queries as quality_queries
    from vintage import build_queries as vintage_queries
    from loan_details import build_queries as loan_queries
    folder=ROOT/'dashboard/sql'
    folder.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,spec in dict(build_queries(),**sales_queries(),**quality_queries(),**vintage_queries(),**loan_queries()).items():
        (folder/(name+'.sql')).write_text(spec['query']+';\n',encoding='utf-8')
        manifest.append(dict(name=name,file='dashboard/sql/'+name+'.sql',parameters=spec['parameters']))
    (ROOT/'dashboard/datasets.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built {} native credit portfolio datasets.'.format(len(manifest)))
