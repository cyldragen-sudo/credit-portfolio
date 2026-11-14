-- Portfolio Overview: stocks at p_as_of, flows from its month start.
WITH scoped AS (
 SELECT * FROM credit.v_snapshot WHERE snapshot_date IN
 ('${p_as_of}'::date,(date_trunc('month','${p_as_of}'::date)-interval '1 day')::date)
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
), current_state AS (
 SELECT coalesce(sum(principal_balance),0) AS portfolio_balance,
 count(*) FILTER(WHERE principal_balance>0) AS active_loans,
 count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) AS active_borrowers,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0) AS exposure_31_plus,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0) AS exposure_91_plus,
 coalesce(sum(overdue_principal),0) AS overdue_principal,
 coalesce(sum(overdue_interest),0) AS overdue_interest
 FROM scoped WHERE snapshot_date='${p_as_of}'::date
), previous_state AS (
 SELECT coalesce(sum(principal_balance),0) AS previous_balance FROM scoped
 WHERE snapshot_date=(date_trunc('month','${p_as_of}'::date)-interval '1 day')::date
), flows AS (
 SELECT coalesce(sum(original_principal),0) AS month_to_date_disbursements
 FROM credit.v_loan_dimension WHERE issue_date BETWEEN date_trunc('month','${p_as_of}'::date)::date AND '${p_as_of}'::date
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
)
SELECT '${p_as_of}'::date AS as_of_date,c.*,p.previous_balance,
 c.portfolio_balance-p.previous_balance AS balance_change,
 (c.portfolio_balance-p.previous_balance)/nullif(p.previous_balance,0) AS balance_change_ratio,
 c.exposure_31_plus/nullif(c.portfolio_balance,0) AS dpd_31_plus_ratio,
 c.exposure_91_plus/nullif(c.portfolio_balance,0) AS dpd_91_plus_ratio,
 f.month_to_date_disbursements
FROM current_state c CROSS JOIN previous_state p CROSS JOIN flows f;
