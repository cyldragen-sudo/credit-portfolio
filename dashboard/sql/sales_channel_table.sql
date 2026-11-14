WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})) SELECT c.channel_id,n.channel_name,count(*) AS submitted_applications,
      count(*) FILTER(WHERE c.approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE c.funded_date<=d.as_of_date) AS cohort_funded_applications,
      to_char(count(*),'FM999,990') AS applications_label,
      coalesce(to_char(count(*) FILTER(WHERE c.approved_date<=d.as_of_date)::numeric/nullif(count(*),0)*100,'FM990.0')||'%','—') AS approval_label,
      coalesce(to_char(count(*) FILTER(WHERE c.funded_date<=d.as_of_date)::numeric/
        nullif(count(*) FILTER(WHERE c.approved_date<=d.as_of_date),0)*100,'FM990.0')||'%','—') AS conversion_label,
      coalesce(to_char(avg(c.funded_date-c.submitted_date) FILTER(WHERE c.funded_date<=d.as_of_date),'FM990.0'),'—') AS days_label
      FROM cohort c CROSS JOIN bounds d JOIN credit.channel n USING(channel_id)
      GROUP BY c.channel_id,n.channel_name ORDER BY c.channel_id;
