"""Cumulative ever-31+ cohorts at completed calendar anniversaries."""
import re
from overview import AS_OF,DEFAULTS,amount_label
from sales import scope

LOCAL_DEFAULTS=dict(p_vintage_page=1,p_vintage_mob_start=1)


def build_queries():
    base="""WITH bounds AS (SELECT {asof} as_of_date,report_start FROM credit.dataset_run),
      loans AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds b
        WHERE l.issue_date BETWEEN b.report_start AND b.as_of_date AND {scope}),
      cohorts AS (SELECT cohort_month,count(*) original_loan_count,sum(original_principal) original_amount,
        row_number() OVER(ORDER BY cohort_month DESC)::integer cohort_row,
        row_number() OVER(ORDER BY cohort_month)::integer curve_order
        FROM loans GROUP BY cohort_month),
      ages AS (SELECT c.*,m.mob,max((l.issue_date+make_interval(months=>m.mob))::date) maturity_date,
        count(a.loan_id) observed_count,count(a.loan_id) FILTER(WHERE a.ever_31_plus) recorded_ever_count
        FROM cohorts c JOIN loans l USING(cohort_month) CROSS JOIN generate_series(1,12) m(mob)
        CROSS JOIN bounds b LEFT JOIN credit.loan_month_age a ON a.loan_id=l.loan_id
          AND a.months_on_book=m.mob AND a.observation_date<=b.as_of_date
        GROUP BY c.cohort_month,c.original_loan_count,c.original_amount,c.cohort_row,c.curve_order,m.mob),
      cells AS (SELECT a.*,
        CASE WHEN maturity_date>b.as_of_date THEN 'Immature'
          WHEN observed_count=original_loan_count THEN 'Observed' ELSE 'Unavailable' END observation_status
        FROM ages a CROSS JOIN bounds b),
      measured AS (SELECT *,CASE WHEN observation_status='Observed' THEN recorded_ever_count END ever_count,
        CASE WHEN observation_status='Observed' THEN recorded_ever_count::numeric/original_loan_count END ever_ratio
        FROM cells)""".format(asof=AS_OF,scope=scope('l'))
    matrix=base+""" SELECT cohort_month,cohort_row,mob,original_loan_count,original_amount,maturity_date,
      observation_status,ever_count,ever_ratio,to_char(cohort_month,'Mon YY') cohort_label,
      to_char(original_loan_count,'FM999,990') count_label,
      CASE WHEN observation_status='Observed' THEN to_char(ever_ratio*100,'FM990.0')||'%' ELSE '—' END cell_label
      FROM measured ORDER BY cohort_row,mob"""
    curves=base+""" SELECT cohort_month,mob,'M'||mob label,to_char(cohort_month,'Mon YY') series,
      ever_ratio*100 value,original_loan_count,ever_count
      FROM measured WHERE observation_status='Observed' AND (curve_order-1)%6=0 AND curve_order<=19
      ORDER BY mob,cohort_month"""
    metrics=[]
    for mob in [3,6,12]:
        key='mob'+str(mob)
        predicate="mob="+str(mob)+" AND observation_status='Observed'"
        metrics.extend(["count(*) FILTER(WHERE "+predicate+") AS "+key+"_cohorts",
            "coalesce(sum(original_loan_count) FILTER(WHERE "+predicate+"),0) AS "+key+"_loans",
            "sum(ever_count) FILTER(WHERE "+predicate+")::numeric/nullif(sum(original_loan_count) FILTER(WHERE "+predicate+"),0) AS "+key+"_ratio"])
    kpis=base+""", totals AS (SELECT count(*) original_loans,coalesce(sum(original_principal),0) original_amount,
      count(DISTINCT cohort_month) cohort_count FROM loans),
      rates AS (SELECT {metrics} FROM measured),
      view_counts AS (SELECT greatest(1,ceil(cohort_count::numeric/6))::integer matrix_page_count FROM totals),
      matrix_view AS (SELECT *,least(greatest(${{INT(p_vintage_page)}},1),matrix_page_count)::integer matrix_page_no,
        CASE WHEN ${{INT(p_vintage_mob_start)}}=7 THEN 7 ELSE 1 END matrix_mob_start FROM view_counts)
      SELECT t.*,r.*,b.as_of_date,to_char(b.as_of_date,'DD Mon YYYY') date_label,
        to_char(t.original_loans,'FM999,990') original_loans_label,
        {amount} original_amount_label,t.cohort_count::text cohort_count_label,
        to_char(b.report_start,'Mon YYYY')||' – '||to_char(b.as_of_date,'Mon YYYY') cohort_window_label,
        CASE WHEN t.original_loans=0 THEN 'No origination cohorts match the selected filters.'
          ELSE 'Original contract counts · Closed and written-off loans remain in the denominator.' END scope_note,
        {labels},p.matrix_page_count,p.matrix_page_no,p.matrix_mob_start,
        greatest(1,p.matrix_page_no-1) matrix_prev_page,
        least(p.matrix_page_count,p.matrix_page_no+1) matrix_next_page,
        CASE WHEN t.cohort_count=0 THEN 'No cohorts · Page 1 of 1'
          ELSE 'Cohorts '||((p.matrix_page_no-1)*6+1)||'–'||least(p.matrix_page_no*6,t.cohort_count)||' of '||t.cohort_count END matrix_page_label
      FROM totals t CROSS JOIN rates r CROSS JOIN bounds b CROSS JOIN matrix_view p""".format(metrics=',\n'.join(metrics),amount=amount_label('t.original_amount'),
        labels=',\n'.join("coalesce(to_char({k}_ratio*100,'FM990.00')||'%','—') {k}_label,"
          " {k}_cohorts||' mature cohorts · '||to_char({k}_loans,'FM999,990')||' loans' {k}_note".format(k='mob'+str(m)) for m in [3,6,12]))
    matrix_view="""WITH all_cells AS ({matrix}),
      view_count AS (SELECT coalesce(max(cohort_row),0) cohort_count FROM all_cells),
      view_bounds AS (SELECT least(greatest(${{INT(p_vintage_page)}},1),greatest(1,ceil(cohort_count::numeric/6)))::integer page_no,
        CASE WHEN ${{INT(p_vintage_mob_start)}}=7 THEN 7 ELSE 1 END mob_start FROM view_count)
      SELECT c.* FROM all_cells c CROSS JOIN view_bounds b
      WHERE c.cohort_row BETWEEN (b.page_no-1)*6+1 AND b.page_no*6
        AND c.mob BETWEEN b.mob_start AND b.mob_start+5 ORDER BY c.cohort_row,c.mob""".format(matrix=matrix)
    datasets=dict(vintage_kpis=kpis,vintage_matrix=matrix,vintage_matrix_view=matrix_view,vintage_curves=curves,
        filter_vintage_mob="SELECT * FROM (VALUES(1,'MOB 1–6'),(7,'MOB 7–12')) ranges(id,label) ORDER BY id")
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    return {name:dict(query=query,parameters={p:defaults[p] for p in defaults if '${INT('+p+')}' in query})
            for name,query in datasets.items()}


def expand(sql,**overrides):
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    params=dict(defaults,**overrides)
    if set(params)!=set(defaults) or any(type(v) is not int or v<0 for v in params.values()):
        raise ValueError('Only known nonnegative integer parameters are allowed')
    return re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(params[m.group(1)]),sql)
