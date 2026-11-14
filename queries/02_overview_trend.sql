SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '${p_start}'::date AND '${p_as_of}'::date
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
GROUP BY snapshot_date ORDER BY snapshot_date;
