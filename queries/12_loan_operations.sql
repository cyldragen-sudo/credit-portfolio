SELECT operation_id,operation_date,operation_type,principal_amount,interest_amount,
 CASE WHEN operation_type IN ('REPAYMENT','PREPAYMENT') THEN principal_amount+interest_amount
 ELSE 0 END AS cash_received
FROM credit.loan_operation WHERE loan_id=${p_loan_id} AND operation_date<='${p_as_of}'::date
ORDER BY operation_date,operation_id;
