SELECT snapshot_date,principal_balance,overdue_principal,overdue_interest,dpd,dpd_bucket,loan_status
FROM credit.loan_snapshot WHERE loan_id=${p_loan_id}
AND snapshot_date BETWEEN '${p_start}'::date AND '${p_as_of}'::date ORDER BY snapshot_date;
