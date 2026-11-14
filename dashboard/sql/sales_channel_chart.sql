WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})) SELECT channel_name AS label,'Disbursements'::text AS series,
      sum(original_principal)/1000000 AS value FROM funded GROUP BY channel_name ORDER BY value DESC;
