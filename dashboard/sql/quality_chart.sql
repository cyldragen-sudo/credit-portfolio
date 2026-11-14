SELECT snapshot_date AS sort_date,to_char(snapshot_date,'Mon YY') label,'31+ DPD'::text series,dpd_31_plus_ratio*100 AS value FROM (SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '2024-11-01'::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
GROUP BY snapshot_date ORDER BY snapshot_date) t UNION ALL SELECT snapshot_date,to_char(snapshot_date,'Mon YY'),'91+ DPD',dpd_91_plus_ratio*100 FROM (SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '2024-11-01'::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
GROUP BY snapshot_date ORDER BY snapshot_date) t ORDER BY sort_date,series;
