SELECT product_name label,'Principal balance'::text series,sum(principal_balance)/1000000000 AS value FROM credit.v_snapshot WHERE snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
      AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
      AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)}) AND principal_balance>0 GROUP BY product_name ORDER BY value DESC;
