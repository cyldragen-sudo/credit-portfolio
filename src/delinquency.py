"""As-of delinquency, same-contract transitions and a bounded loan registry."""
import re
from overview import AS_OF,DEFAULTS,amount_label
from sales import scope

LOCAL_DEFAULTS=dict(p_min_dpd=1,p_quality_page=1)
PAGE_SIZE=8


def build_queries():
    base="""WITH bounds AS (SELECT {asof} AS as_of_date,
      (date_trunc('month',{asof})-interval '1 day')::date AS previous_date,
      date_trunc('month',{asof})::date AS month_start),
    current_rows AS (SELECT s.* FROM credit.v_snapshot s CROSS JOIN bounds b
      WHERE s.snapshot_date=b.as_of_date AND {scope})""".format(asof=AS_OF,scope=scope('s'))
    registry_context=""", eligible AS (SELECT * FROM current_rows WHERE principal_balance>0
      AND loan_status='Active' AND dpd>=greatest(${INT(p_min_dpd)},0)),
    registry_counts AS (SELECT count(*) AS registry_total,
      greatest(1,ceil(count(*)::numeric/8))::integer AS registry_page_count FROM eligible),
    paging AS (SELECT *,least(greatest(${INT(p_quality_page)},1),registry_page_count)::integer AS registry_page_no
      FROM registry_counts)"""
    kpis=base+registry_context+""", summary AS (
      SELECT coalesce(sum(principal_balance),0) AS portfolio_balance,
        coalesce(sum(overdue_principal),0) AS overdue_principal,
        coalesce(sum(overdue_interest),0) AS overdue_interest,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0) AS exposure_31_plus,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0) AS exposure_91_plus,
        count(*) FILTER(WHERE principal_balance>0) AS active_loans,
        count(*) FILTER(WHERE principal_balance>0 AND dpd>0) AS past_due_loans
      FROM current_rows),
    writeoffs AS (SELECT coalesce(sum(o.principal_amount),0) AS monthly_writeoffs
      FROM credit.loan_operation o JOIN credit.v_loan_dimension l USING(loan_id) CROSS JOIN bounds b
      WHERE o.operation_type='WRITE_OFF' AND o.operation_date BETWEEN b.month_start AND b.as_of_date AND {scope}),
    k AS (SELECT s.*,p.*,b.*,w.*,
      s.exposure_31_plus/nullif(s.portfolio_balance,0) AS dpd_31_plus_ratio,
      s.exposure_91_plus/nullif(s.portfolio_balance,0) AS dpd_91_plus_ratio
      FROM summary s CROSS JOIN paging p CROSS JOIN bounds b CROSS JOIN writeoffs w)
    SELECT k.*,{overdue_p} AS overdue_principal_label,{overdue_i} AS overdue_interest_label,
      {writeoff} AS writeoff_label,{exposure31}||' full-loan exposure' AS exposure31_note,
      {exposure91}||' full-loan exposure' AS exposure91_note,
      coalesce(to_char(dpd_31_plus_ratio*100,'FM990.00')||'%','—') AS ratio31_label,
      coalesce(to_char(dpd_91_plus_ratio*100,'FM990.00')||'%','—') AS ratio91_label,
      to_char(past_due_loans,'FM999,990') AS past_due_loans_label,
      to_char(active_loans,'FM999,990')||' active contracts in scope' AS active_loans_note,
      to_char(as_of_date,'DD Mon YYYY') AS date_label,
      to_char(month_start,'Mon YYYY')||' · principal written off' AS writeoff_note,
      to_char(previous_date,'DD Mon YYYY')||' → '||to_char(as_of_date,'DD Mon YYYY')||' · Opening cohort · % and count' AS transition_note,
      'Page '||registry_page_no||' of '||registry_page_count||'   ·   '||to_char(registry_total,'FM999,990')||' loans' AS registry_page_label,
      greatest(1,registry_page_no-1) AS registry_prev_page,
      least(registry_page_count,registry_page_no+1) AS registry_next_page,
      CASE WHEN registry_total=0 THEN 'No loans meet the registry threshold.'
        ELSE 'Ordered by DPD, principal balance and loan ID · amounts in RUB' END AS registry_note,
      CASE WHEN active_loans=0 THEN 'No active loans match the selected filters.'
        ELSE 'Full-loan exposure includes overdue principal. Registry threshold affects the loan list only.' END AS scope_note
    FROM k""".format(scope=scope('l'),overdue_p=amount_label('overdue_principal'),
                      overdue_i=amount_label('overdue_interest'),writeoff=amount_label('monthly_writeoffs'),
                      exposure31=amount_label('exposure_31_plus'),exposure91=amount_label('exposure_91_plus'))
    # Format only the static SQL above; keep FineReport INT macros literal.
    buckets=base+""", states(ord,label) AS (VALUES (0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+')),
      grouped AS (SELECT dpd_bucket,count(*) AS active_loans,sum(principal_balance) balance
        FROM current_rows WHERE principal_balance>0 GROUP BY dpd_bucket)
      SELECT s.label,'Principal exposure'::text AS series,coalesce(g.balance,0)/1000000000 AS value,
        coalesce(g.active_loans,0) AS active_loans
      FROM states s LEFT JOIN grouped g ON g.dpd_bucket=s.label
      WHERE EXISTS(SELECT 1 FROM current_rows WHERE principal_balance>0) ORDER BY s.ord"""
    transitions="""WITH bounds AS (SELECT {asof} AS as_of_date,
      (date_trunc('month',{asof})-interval '1 day')::date AS previous_date),
      states(ord,bucket) AS (VALUES(0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+'),(5,'Closed'),(6,'Written Off')),
      pairs AS (SELECT a.loan_id,
        CASE WHEN a.loan_status='Active' THEN a.dpd_bucket ELSE a.loan_status END AS from_bucket,
        CASE WHEN z.loan_status='Active' THEN z.dpd_bucket ELSE z.loan_status END AS to_bucket
        FROM credit.loan_snapshot a JOIN credit.loan_snapshot z USING(loan_id)
        JOIN credit.v_loan_dimension l USING(loan_id) CROSS JOIN bounds b
        WHERE a.snapshot_date=b.previous_date AND z.snapshot_date=b.as_of_date AND {scope}),
      opening AS (SELECT from_bucket,count(*) AS opening_loans FROM pairs GROUP BY from_bucket),
      movement AS (SELECT from_bucket,to_bucket,count(*) AS loan_count FROM pairs GROUP BY 1,2),
      cells AS (SELECT f.ord AS from_order,t.ord AS to_order,f.bucket AS from_bucket,t.bucket AS to_bucket,
        coalesce(o.opening_loans,0) AS opening_loans,coalesce(m.loan_count,0) AS loan_count,
        coalesce(m.loan_count,0)::numeric/nullif(o.opening_loans,0) AS transition_ratio
        FROM states f CROSS JOIN states t LEFT JOIN opening o ON o.from_bucket=f.bucket
        LEFT JOIN movement m ON m.from_bucket=f.bucket AND m.to_bucket=t.bucket)
      SELECT *,from_bucket||' ('||to_char(opening_loans,'FM999,990')||')' AS row_label,
        CASE WHEN opening_loans=0 THEN '—' WHEN loan_count=0 THEN '0%'
        ELSE to_char(transition_ratio*100,'FM990.0')||'% · '||to_char(loan_count,'FM999,990') END AS cell_label
      FROM cells ORDER BY from_order,to_order""".format(asof=AS_OF,scope=scope('l'))
    registry=base+registry_context+""", ordered AS (SELECT *,row_number() OVER(
      ORDER BY dpd DESC,principal_balance DESC,loan_id) AS registry_row_no FROM eligible)
      SELECT e.snapshot_date,e.loan_id,e.loan_reference,e.customer_label,e.product_name,e.region_name,e.channel_name,
        e.principal_balance,e.overdue_principal,e.overdue_interest,e.dpd,e.dpd_bucket,
        to_char(e.principal_balance,'FM999,999,990.00') AS balance_label,
        to_char(e.overdue_principal,'FM999,999,990.00') AS overdue_principal_label,
        to_char(e.overdue_interest,'FM999,999,990.00') AS overdue_interest_label,
        e.dpd::text AS dpd_label,e.registry_row_no
      FROM ordered e CROSS JOIN paging p
      WHERE e.registry_row_no BETWEEN (p.registry_page_no-1)*8+1 AND p.registry_page_no*8
      ORDER BY e.registry_row_no"""
    filters="SELECT * FROM (VALUES (0,'All active'),(1,'1+ DPD'),(31,'31+ DPD'),(91,'91+ DPD')) options(id,label) ORDER BY id"
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    queries=dict(quality_kpis=kpis,quality_buckets=buckets,quality_transitions=transitions,
                 quality_registry=registry,filter_min_dpd=filters)
    return {name:dict(query=query,parameters={p:defaults[p] for p in defaults if '${INT('+p+')}' in query})
            for name,query in queries.items()}


def expand(sql,**overrides):
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    params=dict(defaults,**overrides)
    if set(params)!=set(defaults) or any(type(v) is not int or v<0 for v in params.values()):
        raise ValueError('Only known nonnegative integer parameters are allowed')
    return re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(params[m.group(1)]),sql)
