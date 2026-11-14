SELECT product_id,product_name,region_id,region_name,
 sum(principal_balance) AS portfolio_balance,
 count(*) FILTER(WHERE principal_balance>0) AS active_loans,
 count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) AS active_borrowers,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_snapshot WHERE snapshot_date='${p_as_of}'::date
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
GROUP BY product_id,product_name,region_id,region_name ORDER BY portfolio_balance DESC;
