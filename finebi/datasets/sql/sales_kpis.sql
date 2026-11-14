-- Dataset: Sales KPIs
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})), cohort_counts AS (SELECT count(*) AS submitted_applications,
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
      FROM cohort_counts c CROSS JOIN flow_counts f CROSS JOIN bounds d) SELECT k.*,
      CASE WHEN abs(funded_amount)>=1000000000 THEN 'RUB '||to_char(funded_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(funded_amount/1000000,'FM999,990.00')||' m' END AS funded_amount_label,
      to_char(funded_loans,'FM999,999,990') AS funded_loans_label,
      coalesce(CASE WHEN abs(average_funded_amount)>=1000000000 THEN 'RUB '||to_char(average_funded_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(average_funded_amount/1000000,'FM999,990.00')||' m' END,'—') AS average_amount_label,
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
      FROM k
