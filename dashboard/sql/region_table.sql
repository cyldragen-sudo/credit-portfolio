WITH states AS (SELECT * FROM credit.v_snapshot WHERE snapshot_date IN ((SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date),
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date) AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
      AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
      AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})),
      current_state AS (SELECT region_id,region_name,sum(principal_balance) balance,
        count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) borrowers,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) ratio31,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) ratio91
        FROM states WHERE snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2),
      previous_state AS (SELECT region_id,sum(principal_balance) balance FROM states
        WHERE snapshot_date=(date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date GROUP BY 1)
      SELECT c.region_id,c.region_name,c.balance,c.borrowers,c.ratio31,c.ratio91,
      to_char(c.balance/1000000000,'FM990.00') AS balance_label,
      coalesce(CASE WHEN c.balance>=p.balance THEN '+' ELSE '' END||to_char((c.balance-p.balance)/nullif(p.balance,0)*100,'FM990.00')||'%','—') AS growth_label,
      to_char(c.borrowers,'FM999,990') AS borrowers_label,
      coalesce(to_char(c.ratio31*100,'FM990.00')||'%','—') AS ratio31_label,
      coalesce(to_char(c.ratio91*100,'FM990.00')||'%','—') AS ratio91_label
      FROM current_state c LEFT JOIN previous_state p USING(region_id) ORDER BY c.balance DESC,c.region_id;
