-- Dataset: Sales Plan vs Actual
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = October 2026 (Text), p_product_id = All Products (Text), p_region_id = All Regions (Text)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${IF(p_date_key="October 2026",20261031,IF(p_date_key="September 2026",20260930,IF(p_date_key="August 2026",20260831,IF(p_date_key="July 2026",20260731,IF(p_date_key="June 2026",20260630,IF(p_date_key="May 2026",20260531,IF(p_date_key="April 2026",20260430,IF(p_date_key="March 2026",20260331,IF(p_date_key="February 2026",20260228,IF(p_date_key="January 2026",20260131,IF(p_date_key="December 2025",20251231,IF(p_date_key="November 2025",20251130,IF(p_date_key="October 2025",20251031,IF(p_date_key="September 2025",20250930,IF(p_date_key="August 2025",20250831,IF(p_date_key="July 2025",20250731,IF(p_date_key="June 2025",20250630,IF(p_date_key="May 2025",20250531,IF(p_date_key="April 2025",20250430,IF(p_date_key="March 2025",20250331,IF(p_date_key="February 2025",20250228,IF(p_date_key="January 2025",20250131,IF(p_date_key="December 2024",20241231,IF(p_date_key="November 2024",20241130,INT(p_date_key)))))))))))))))))))))))))}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${IF(p_date_key="October 2026",20261031,IF(p_date_key="September 2026",20260930,IF(p_date_key="August 2026",20260831,IF(p_date_key="July 2026",20260731,IF(p_date_key="June 2026",20260630,IF(p_date_key="May 2026",20260531,IF(p_date_key="April 2026",20260430,IF(p_date_key="March 2026",20260331,IF(p_date_key="February 2026",20260228,IF(p_date_key="January 2026",20260131,IF(p_date_key="December 2025",20251231,IF(p_date_key="November 2025",20251130,IF(p_date_key="October 2025",20251031,IF(p_date_key="September 2025",20250930,IF(p_date_key="August 2025",20250831,IF(p_date_key="July 2025",20250731,IF(p_date_key="June 2025",20250630,IF(p_date_key="May 2025",20250531,IF(p_date_key="April 2025",20250430,IF(p_date_key="March 2025",20250331,IF(p_date_key="February 2025",20250228,IF(p_date_key="January 2025",20250131,IF(p_date_key="December 2024",20241231,IF(p_date_key="November 2024",20241130,INT(p_date_key)))))))))))))))))))))))))}
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
      WHERE p.plan_month=d.month_start AND (${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))}=0 OR p.product_id=${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))})
      AND (${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))}=0 OR b.region_id=${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))})
      GROUP BY p.product_id,n.product_name ORDER BY p.product_id
