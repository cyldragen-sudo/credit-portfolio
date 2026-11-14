-- Whole-month targets; deliberately has no channel filter. Current month actuals are to p_as_of.
WITH actual AS (
 SELECT date_trunc('month',issue_date)::date AS plan_month,product_id,branch_id,
 sum(original_principal) AS funded_amount,count(*) AS funded_count
 FROM credit.loan WHERE issue_date<='${p_as_of}'::date GROUP BY 1,2,3
)
SELECT p.plan_month,p.product_id,d.product_name,p.branch_id,b.branch_name,r.region_name,
 p.planned_amount,p.planned_count,coalesce(a.funded_amount,0) AS funded_amount,
 coalesce(a.funded_count,0) AS funded_count,
 coalesce(a.funded_amount,0)/nullif(p.planned_amount,0) AS plan_attainment
FROM credit.sales_plan p LEFT JOIN actual a USING(plan_month,product_id,branch_id)
JOIN credit.product d USING(product_id) JOIN credit.branch b USING(branch_id) JOIN credit.region r USING(region_id)
WHERE p.plan_month BETWEEN date_trunc('month','${p_start}'::date)::date
 AND date_trunc('month',least('${p_end}'::date,'${p_as_of}'::date))::date
 AND (${p_product_id}=0 OR p.product_id=${p_product_id})
 AND (${p_region_id}=0 OR b.region_id=${p_region_id})
ORDER BY 1,2,4;
