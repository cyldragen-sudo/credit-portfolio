SELECT dpd_bucket,count(*) AS active_loans,sum(principal_balance) AS principal_exposure,
 sum(overdue_principal) AS overdue_principal,sum(overdue_interest) AS overdue_interest,
 sum(principal_balance)/nullif(sum(sum(principal_balance)) OVER(),0) AS portfolio_share
FROM credit.v_snapshot WHERE snapshot_date='${p_as_of}'::date AND principal_balance>0
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
GROUP BY dpd_bucket ORDER BY CASE dpd_bucket WHEN '0' THEN 0 WHEN '1-30' THEN 1
 WHEN '31-60' THEN 2 WHEN '61-90' THEN 3 ELSE 4 END;
