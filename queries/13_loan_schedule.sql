WITH allocations AS (
 SELECT a.loan_id,a.schedule_version,a.installment_no,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type<>'WRITE_OFF'),0) AS principal_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type<>'WRITE_OFF'),0) AS interest_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type='WRITE_OFF'),0) AS principal_written_off,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type='WRITE_OFF'),0) AS interest_written_off
 FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
 WHERE a.loan_id=${p_loan_id} AND o.operation_date<='${p_as_of}'::date GROUP BY 1,2,3
)
SELECT s.installment_no,s.due_date,s.principal_due,s.interest_due,
 coalesce(a.principal_paid,0) AS principal_paid,coalesce(a.interest_paid,0) AS interest_paid,
 coalesce(a.principal_written_off,0) AS principal_written_off,
 coalesce(a.interest_written_off,0) AS interest_written_off,
 CASE WHEN s.cancelled_on<='${p_as_of}'::date THEN s.cancelled_on END AS cancelled_on,
 CASE WHEN s.due_date<'${p_as_of}'::date THEN s.principal_due-coalesce(a.principal_paid,0)-coalesce(a.principal_written_off,0) ELSE 0 END AS overdue_principal,
 CASE WHEN s.due_date<'${p_as_of}'::date AND (s.cancelled_on IS NULL OR s.cancelled_on>'${p_as_of}'::date)
 THEN s.interest_due-coalesce(a.interest_paid,0)-coalesce(a.interest_written_off,0) ELSE 0 END AS overdue_interest
FROM credit.payment_schedule s LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
WHERE s.loan_id=${p_loan_id} AND s.effective_from<='${p_as_of}'::date ORDER BY s.installment_no;
