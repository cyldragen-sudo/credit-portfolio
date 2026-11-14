-- Dataset: Application Funnel
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
      FROM cohort_counts c CROSS JOIN flow_counts f CROSS JOIN bounds d) SELECT stage,label,'Applications'::text AS series,value
      FROM k CROSS JOIN LATERAL (VALUES
        (1,'Submitted',submitted_applications),(2,'Approved',approved_applications),
        (3,'Funded',cohort_funded_applications)) stages(stage,label,value)
      WHERE submitted_applications>0 ORDER BY stage
