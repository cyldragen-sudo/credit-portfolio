SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<='${p_as_of}'::date THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<='${p_as_of}'::date THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${p_loan_id} AND s.snapshot_date='${p_as_of}'::date;
