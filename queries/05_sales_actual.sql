-- Funded-date flow, distinct from the submission-date funnel cohort.
SELECT date_trunc('month',issue_date)::date AS funding_month,
 product_id,product_name,channel_id,channel_name,region_id,region_name,
 count(*) AS funded_loans,sum(original_principal) AS funded_amount,
 avg(original_principal) AS average_funded_amount,
 sum(original_principal*annual_rate)/nullif(sum(original_principal),0) AS original_amount_weighted_rate
FROM credit.v_loan_dimension
WHERE issue_date BETWEEN '${p_start}'::date AND least('${p_end}'::date,'${p_as_of}'::date)
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
GROUP BY 1,product_id,product_name,channel_id,channel_name,region_id,region_name ORDER BY 1,2,4,6;
