-- Dataset: Loan Details KPIs
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
 AND calendar_date BETWEEN report_start AND as_of_date)),
      operations AS (SELECT o.* FROM (SELECT operation_id,operation_date,operation_type,principal_amount,interest_amount,
 CASE WHEN operation_type IN ('REPAYMENT','PREPAYMENT') THEN principal_amount+interest_amount
 ELSE 0 END AS cash_received
FROM credit.loan_operation WHERE loan_id=${INT(p_loan_id)} AND operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
ORDER BY operation_date,operation_id) o WHERE EXISTS(SELECT 1 FROM selected)),
      schedule AS (SELECT s.*,s.principal_paid+s.interest_paid paid_amount,
        s.principal_written_off+s.interest_written_off written_off_amount
        FROM (WITH allocations AS (
 SELECT a.loan_id,a.schedule_version,a.installment_no,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type<>'WRITE_OFF'),0) AS principal_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type<>'WRITE_OFF'),0) AS interest_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type='WRITE_OFF'),0) AS principal_written_off,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type='WRITE_OFF'),0) AS interest_written_off
 FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
 WHERE a.loan_id=${INT(p_loan_id)} AND o.operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2,3
)
SELECT s.installment_no,s.due_date,s.principal_due,s.interest_due,
 coalesce(a.principal_paid,0) AS principal_paid,coalesce(a.interest_paid,0) AS interest_paid,
 coalesce(a.principal_written_off,0) AS principal_written_off,
 coalesce(a.interest_written_off,0) AS interest_written_off,
 CASE WHEN s.cancelled_on<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.cancelled_on END AS cancelled_on,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.principal_due-coalesce(a.principal_paid,0)-coalesce(a.principal_written_off,0) ELSE 0 END AS overdue_principal,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (s.cancelled_on IS NULL OR s.cancelled_on>(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))
 THEN s.interest_due-coalesce(a.interest_paid,0)-coalesce(a.interest_written_off,0) ELSE 0 END AS overdue_interest
FROM credit.payment_schedule s LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
WHERE s.loan_id=${INT(p_loan_id)} AND s.effective_from<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) ORDER BY s.installment_no) s WHERE EXISTS(SELECT 1 FROM selected)),
      counts AS (SELECT (SELECT count(*) FROM operations) operation_count,
        (SELECT count(*) FROM schedule) schedule_count) SELECT h.*,p.*,coalesce(h.loan_id,0) selected_loan_id,(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date,to_char((SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date),'DD Mon YYYY') date_label,CASE WHEN h.loan_id IS NULL THEN 'No loan selected' ELSE h.loan_reference||' · '||h.customer_label||' · '||h.product_name END identity_label,CASE WHEN h.loan_id IS NULL THEN CASE WHEN ${INT(p_loan_id)}=0 THEN 'Open a loan from Portfolio Quality to view its details.' ELSE 'This loan is not available as of the selected date.' END ELSE 'Contract follows loan ID and As of; portfolio filters are retained for return.' END scope_note,CASE WHEN h.loan_id IS NULL THEN '—' ELSE h.dpd::text END dpd_label,coalesce(h.loan_status,'—') status_label,coalesce(to_char(h.issue_date,'DD Mon YYYY'),'—') issue_label,coalesce(to_char(h.maturity_date,'DD Mon YYYY'),'—') maturity_label,coalesce(to_char(h.actual_close_date,'DD Mon YYYY'),'—') close_label,coalesce(to_char(h.annual_rate,'FM990.00')||'%','—') rate_label,coalesce(h.term_months||' months','—') term_label,coalesce(h.region_name||' · '||h.branch_name||' · '||h.channel_name||' · Origination risk: '||h.risk_at_origination,'Select a contract in the loan registry.') origination_label,coalesce((SELECT sum(cash_received) FROM operations),0) cash_received,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.principal_balance,'FM999,999,999,990.00') END balance_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.overdue_principal,'FM999,999,999,990.00') END overdue_principal_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.overdue_interest,'FM999,999,999,990.00') END overdue_interest_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.original_principal,'FM999,999,999,990.00') END original_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(coalesce((SELECT sum(cash_received) FROM operations),0),'FM999,999,999,990.00') END cash_label FROM counts p LEFT JOIN selected h ON true
