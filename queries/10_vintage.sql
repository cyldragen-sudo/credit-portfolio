-- Original-contract denominator; a cell is returned only when the entire selected cohort has matured.
WITH loans AS (
 SELECT * FROM credit.v_loan_dimension
 WHERE issue_date BETWEEN '${p_start}'::date AND least('${p_end}'::date,'${p_as_of}'::date)
 AND (${p_product_id}=0 OR product_id=${p_product_id})
 AND (${p_channel_id}=0 OR channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR region_id=${p_region_id})
 AND (${p_risk_id}=0 OR risk_at_origination=CASE ${p_risk_id} WHEN 1 THEN 'Low' WHEN 2 THEN 'Medium' WHEN 3 THEN 'High' END)
)
SELECT l.cohort_month,m.months_on_book,count(*) AS original_loan_count,
 count(a.loan_id) FILTER(WHERE a.ever_31_plus) AS ever_31_plus_count,
 count(a.loan_id) FILTER(WHERE a.ever_31_plus)::numeric/count(*) AS ever_31_plus_ratio
FROM loans l CROSS JOIN generate_series(1,36) AS m(months_on_book)
LEFT JOIN credit.loan_month_age a ON a.loan_id=l.loan_id AND a.months_on_book=m.months_on_book
 AND a.observation_date<='${p_as_of}'::date
GROUP BY l.cohort_month,m.months_on_book
HAVING count(a.loan_id)=count(*) ORDER BY 1,2;
