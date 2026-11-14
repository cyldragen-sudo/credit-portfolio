"""Monthly funded-date sales and submission-cohort funnel datasets."""
from overview import AS_OF, DEFAULTS, amount_label


def scope(alias,include_channel=True):
    parts=[f'(${{INT(p_product_id)}}=0 OR {alias}.product_id=${{INT(p_product_id)}})',
           f'(${{INT(p_region_id)}}=0 OR {alias}.region_id=${{INT(p_region_id)}})']
    if include_channel:
        parts.append(f'(${{INT(p_channel_id)}}=0 OR {alias}.channel_id=${{INT(p_channel_id)}})')
    return ' AND '.join(parts)


def build_queries():
    base="""WITH bounds AS (SELECT {asof} AS as_of_date,date_trunc('month',{asof})::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND {apps}),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND {loans})""".format(
        asof=AS_OF,apps=scope('a'),loans=scope('l'))
    counts=""", cohort_counts AS (SELECT count(*) AS submitted_applications,
      count(*) FILTER(WHERE approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE funded_date<=d.as_of_date) AS cohort_funded_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Declined') AS declined_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Withdrawn') AS withdrawn_applications,
      count(*) FILTER(WHERE (funded_date IS NULL OR funded_date>d.as_of_date)
        AND (terminal_date IS NULL OR terminal_date>d.as_of_date)) AS in_progress_applications,
      avg(funded_date-submitted_date) FILTER(WHERE funded_date<=d.as_of_date) AS average_days_to_funding
      FROM cohort CROSS JOIN bounds d),
    flow_counts AS (SELECT count(*) AS funded_loans,coalesce(sum(original_principal),0) AS funded_amount,
      avg(original_principal) AS average_funded_amount FROM funded),
    k AS (SELECT c.*,f.*,d.*,c.approved_applications::numeric/nullif(c.submitted_applications,0) AS approval_ratio,
      c.cohort_funded_applications::numeric/nullif(c.approved_applications,0) AS approved_to_funded_ratio
      FROM cohort_counts c CROSS JOIN flow_counts f CROSS JOIN bounds d)"""
    kpi=base+counts+""" SELECT k.*,
      {amount} AS funded_amount_label,
      to_char(funded_loans,'FM999,999,990') AS funded_loans_label,
      coalesce({average},'—') AS average_amount_label,
      to_char(submitted_applications,'FM999,999,990') AS applications_label,
      coalesce(to_char(approval_ratio*100,'FM990.00')||'%','—') AS approval_label,
      coalesce(to_char(approved_to_funded_ratio*100,'FM990.00')||'%','—') AS conversion_label,
      to_char(approved_applications,'FM999,999,990')||' approved applications' AS approval_note,
      to_char(cohort_funded_applications,'FM999,999,990')||' funded from submission cohort' AS conversion_note,
      coalesce(to_char(as_of_date,'DD Mon YYYY'),'No reporting date') AS date_label,
      coalesce(to_char(as_of_date,'FMMonth YYYY'),'No reporting date') AS month_label,
      'Declined: '||declined_applications||'   ·   Withdrawn: '||withdrawn_applications||'   ·   In progress: '||in_progress_applications AS funnel_summary,
      'Avg time to funding: '||coalesce(to_char(average_days_to_funding,'FM990.0')||' days','—') AS funding_time_label,
      'Submitted in '||to_char(as_of_date,'Mon YYYY')||' · Outcomes through '||to_char(as_of_date,'DD Mon YYYY') AS cohort_note,
      CASE WHEN submitted_applications=0 AND funded_loans=0 THEN 'No sales or applications match the selected filters.'
      ELSE 'Submission cohorts and funded-date sales are separate populations. Recent applications may still be in progress.' END AS scope_note
      FROM k""".format(amount=amount_label('funded_amount'),average=amount_label('average_funded_amount'))
    funnel=base+counts+""" SELECT stage,label,'Applications'::text AS series,value
      FROM k CROSS JOIN LATERAL (VALUES
        (1,'Submitted',submitted_applications),(2,'Approved',approved_applications),
        (3,'Funded',cohort_funded_applications)) stages(stage,label,value)
      WHERE submitted_applications>0 ORDER BY stage"""
    trend="""WITH bounds AS (SELECT {asof} as_of_date),loans AS (
      SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN '2024-11-01'::date AND d.as_of_date AND {scope}),
      monthly AS (SELECT date_trunc('month',issue_date)::date month_start,sum(original_principal) amount FROM loans GROUP BY 1)
      SELECT c.calendar_date AS month_end,to_char(c.calendar_date,'Mon YY') label,
      'Disbursements'::text series,coalesce(m.amount,0)/1000000 AS value
      FROM credit.calendar c CROSS JOIN bounds d LEFT JOIN monthly m ON m.month_start=c.month_start
      WHERE c.calendar_date=c.month_end AND c.calendar_date BETWEEN '2024-11-01'::date AND d.as_of_date
      AND EXISTS(SELECT 1 FROM loans) ORDER BY c.calendar_date""".format(asof=AS_OF,scope=scope('l'))
    channel_chart=base+""" SELECT channel_name AS label,'Disbursements'::text AS series,
      sum(original_principal)/1000000 AS value FROM funded GROUP BY channel_name ORDER BY value DESC"""
    plan="""WITH bounds AS (SELECT {asof} AS as_of_date,date_trunc('month',{asof})::date AS month_start),
      actual AS (SELECT l.product_id,l.branch_id,count(*) AS funded_loans,sum(l.original_principal) amount
        FROM credit.loan l CROSS JOIN bounds d WHERE l.issue_date BETWEEN d.month_start AND d.as_of_date GROUP BY 1,2)
      SELECT p.product_id,n.product_name,sum(coalesce(a.funded_loans,0)) AS funded_loans,
        sum(coalesce(a.amount,0)) AS funded_amount,sum(p.planned_amount) AS planned_amount,
        sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0) AS plan_attainment,
        to_char(sum(coalesce(a.funded_loans,0)),'FM999,990') AS loans_label,
        to_char(sum(coalesce(a.amount,0))/1000000,'FM999,990.00') AS actual_label,
        to_char(sum(p.planned_amount)/1000000,'FM999,990.00') AS plan_label,
        coalesce(to_char(sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0)*100,'FM990.0')||'%','—') AS attainment_label
      FROM credit.sales_plan p CROSS JOIN bounds d JOIN credit.product n USING(product_id)
      JOIN credit.branch b USING(branch_id) LEFT JOIN actual a ON a.product_id=p.product_id AND a.branch_id=p.branch_id
      WHERE p.plan_month=d.month_start AND (${{INT(p_product_id)}}=0 OR p.product_id=${{INT(p_product_id)}})
      AND (${{INT(p_region_id)}}=0 OR b.region_id=${{INT(p_region_id)}})
      GROUP BY p.product_id,n.product_name ORDER BY p.product_id""".format(asof=AS_OF)
    channels=base+""" SELECT c.channel_id,n.channel_name,count(*) AS submitted_applications,
      count(*) FILTER(WHERE c.approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE c.funded_date<=d.as_of_date) AS cohort_funded_applications,
      to_char(count(*),'FM999,990') AS applications_label,
      coalesce(to_char(count(*) FILTER(WHERE c.approved_date<=d.as_of_date)::numeric/nullif(count(*),0)*100,'FM990.0')||'%','—') AS approval_label,
      coalesce(to_char(count(*) FILTER(WHERE c.funded_date<=d.as_of_date)::numeric/
        nullif(count(*) FILTER(WHERE c.approved_date<=d.as_of_date),0)*100,'FM990.0')||'%','—') AS conversion_label,
      coalesce(to_char(avg(c.funded_date-c.submitted_date) FILTER(WHERE c.funded_date<=d.as_of_date),'FM990.0'),'—') AS days_label
      FROM cohort c CROSS JOIN bounds d JOIN credit.channel n USING(channel_id)
      GROUP BY c.channel_id,n.channel_name ORDER BY c.channel_id"""
    queries=dict(sales_kpis=kpi,sales_funnel_chart=funnel,sales_trend_chart=trend,
                 sales_channel_chart=channel_chart,sales_plan_table=plan,sales_channel_table=channels)
    return {name:dict(query=query,parameters={p:DEFAULTS[p] for p in DEFAULTS if '${INT('+p+')}' in query})
            for name,query in queries.items()}
