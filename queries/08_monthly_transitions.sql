-- Last completed calendar month; denominator is contracts in the opening bucket.
SELECT from_date,to_date,from_bucket,to_bucket,count(*) AS loan_count,
 count(*)::numeric/sum(count(*)) OVER(PARTITION BY from_date,from_bucket) AS transition_ratio,
 sum(opening_principal) AS opening_principal,sum(closing_principal) AS closing_principal
FROM credit.v_monthly_transition
WHERE to_date=(date_trunc('month','${p_as_of}'::date+1)-interval '1 day')::date
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
GROUP BY from_date,to_date,from_bucket,to_bucket ORDER BY from_bucket,to_bucket;
