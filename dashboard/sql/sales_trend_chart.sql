WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date),loans AS (
      SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN '2024-11-01'::date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})),
      monthly AS (SELECT date_trunc('month',issue_date)::date month_start,sum(original_principal) amount FROM loans GROUP BY 1)
      SELECT c.calendar_date AS month_end,to_char(c.calendar_date,'Mon YY') label,
      'Disbursements'::text series,coalesce(m.amount,0)/1000000 AS value
      FROM credit.calendar c CROSS JOIN bounds d LEFT JOIN monthly m ON m.month_start=c.month_start
      WHERE c.calendar_date=c.month_end AND c.calendar_date BETWEEN '2024-11-01'::date AND d.as_of_date
      AND EXISTS(SELECT 1 FROM loans) ORDER BY c.calendar_date;
