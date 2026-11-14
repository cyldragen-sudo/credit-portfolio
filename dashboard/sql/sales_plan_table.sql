WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS month_start),
      actual AS (SELECT l.product_id,l.branch_id,count(*) AS funded_loans,sum(l.original_principal) amount
        FROM credit.loan l CROSS JOIN bounds d WHERE l.issue_date BETWEEN d.month_start AND d.as_of_date GROUP BY 1,2)
      SELECT p.product_id,n.product_name,sum(coalesce(a.funded_loans,0)) AS funded_loans,
        sum(coalesce(a.amount,0)) AS funded_amount,sum(p.planned_amount) AS planned_amount,
        sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0) AS plan_attainment,
        to_char(sum(coalesce(a.funded_loans,0)),'FM999,990') AS loans_label,
        to_char(sum(coalesce(a.amount,0))/1000000,'FM999,990.00') AS actual_label,
        to_char(sum(p.planned_amount)/1000000,'FM999,990.00') AS plan_label,
        coalesce(to_char(sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0)*100,'FM990.0')||'%','—') AS attainment_label
      FROM credit.sales_plan p CROSS JOIN bounds d JOIN credit.product n USING(product_id)
      JOIN credit.branch b USING(branch_id) LEFT JOIN actual a ON a.product_id=p.product_id AND a.branch_id=p.branch_id
      WHERE p.plan_month=d.month_start AND (${INT(p_product_id)}=0 OR p.product_id=${INT(p_product_id)})
      AND (${INT(p_region_id)}=0 OR b.region_id=${INT(p_region_id)})
      GROUP BY p.product_id,n.product_name ORDER BY p.product_id;
