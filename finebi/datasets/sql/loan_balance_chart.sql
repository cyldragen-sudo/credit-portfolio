-- Dataset: Loan Balance History
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)) SELECT s.snapshot_date,to_char(s.snapshot_date,'Mon YY') label,
      'Principal balance'::text series,s.principal_balance/1000000 value FROM credit.loan_snapshot s JOIN credit.calendar c ON c.calendar_date=s.snapshot_date
      CROSS JOIN credit.dataset_run d WHERE s.loan_id=${INT(p_loan_id)} AND EXISTS(SELECT 1 FROM selected)
      AND s.snapshot_date BETWEEN d.report_start AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND s.snapshot_date=c.month_end ORDER BY s.snapshot_date
