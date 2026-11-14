SELECT loan_id,loan_reference,customer_label,product_name,channel_name,region_name,
 principal_balance,overdue_principal,overdue_interest,dpd,dpd_bucket,loan_status
FROM credit.v_snapshot WHERE snapshot_date='${p_as_of}'::date
 AND dpd>=${p_min_dpd}
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
ORDER BY dpd DESC,principal_balance DESC,loan_id LIMIT 200 OFFSET ${p_offset};
