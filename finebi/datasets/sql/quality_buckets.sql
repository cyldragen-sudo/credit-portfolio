-- Dataset: DPD Bucket Exposure
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date AS previous_date,
      date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS month_start),
    current_rows AS (SELECT s.* FROM credit.v_snapshot s CROSS JOIN bounds b
      WHERE s.snapshot_date=b.as_of_date AND (${INT(p_product_id)}=0 OR s.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR s.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR s.channel_id=${INT(p_channel_id)})), states(ord,label) AS (VALUES (0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+')),
      grouped AS (SELECT dpd_bucket,count(*) AS active_loans,sum(principal_balance) balance
        FROM current_rows WHERE principal_balance>0 GROUP BY dpd_bucket)
      SELECT s.label,'Principal exposure'::text AS series,coalesce(g.balance,0)/1000000000 AS value,
        coalesce(g.active_loans,0) AS active_loans
      FROM states s LEFT JOIN grouped g ON g.dpd_bucket=s.label
      WHERE EXISTS(SELECT 1 FROM current_rows WHERE principal_balance>0) ORDER BY s.ord
