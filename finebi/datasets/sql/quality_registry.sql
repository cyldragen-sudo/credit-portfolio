-- Dataset: Loan Registry
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number), p_min_dpd = 1 (Number)

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
      WHERE s.snapshot_date=b.as_of_date AND (${INT(p_product_id)}=0 OR s.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR s.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR s.channel_id=${INT(p_channel_id)})), eligible AS (SELECT * FROM current_rows WHERE principal_balance>0
      AND loan_status='Active' AND dpd>=greatest(${INT(p_min_dpd)},0)),
    ordered AS (SELECT *,row_number() OVER(
      ORDER BY dpd DESC,principal_balance DESC,loan_id) AS registry_row_no FROM eligible)
      SELECT e.snapshot_date,e.loan_id,e.loan_reference,e.customer_label,e.product_name,e.region_name,e.channel_name,
        e.principal_balance,e.overdue_principal,e.overdue_interest,e.dpd,e.dpd_bucket,
        to_char(e.principal_balance,'FM999,999,990.00') AS balance_label,
        to_char(e.overdue_principal,'FM999,999,990.00') AS overdue_principal_label,
        to_char(e.overdue_interest,'FM999,999,990.00') AS overdue_interest_label,
        e.dpd::text AS dpd_label,e.registry_row_no
      FROM ordered e
      ORDER BY e.registry_row_no
