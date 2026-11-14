-- Application submission cohort; subsequent outcomes are observed only through p_as_of.
WITH cohort AS (
 SELECT a.* FROM credit.application a JOIN credit.branch b USING(branch_id)
 WHERE submitted_date BETWEEN '${p_start}'::date AND least('${p_end}'::date,'${p_as_of}'::date)
 AND (${p_product_id}=0 OR a.product_id=${p_product_id})
 AND (${p_channel_id}=0 OR a.channel_id=${p_channel_id})
 AND (${p_region_id}=0 OR b.region_id=${p_region_id})
), counts AS (
 SELECT count(*) AS submitted_applications,
 count(*) FILTER(WHERE approved_date<='${p_as_of}'::date) AS approved_applications,
 count(*) FILTER(WHERE funded_date<='${p_as_of}'::date) AS funded_applications,
 count(*) FILTER(WHERE terminal_date<='${p_as_of}'::date AND outcome='Declined') AS declined_applications,
 count(*) FILTER(WHERE terminal_date<='${p_as_of}'::date AND outcome='Withdrawn') AS withdrawn_applications,
 count(*) FILTER(WHERE (funded_date IS NULL OR funded_date>'${p_as_of}'::date)
 AND (terminal_date IS NULL OR terminal_date>'${p_as_of}'::date)) AS in_progress_applications,
 avg(funded_date-submitted_date) FILTER(WHERE funded_date<='${p_as_of}'::date) AS average_days_to_funding
 FROM cohort
)
SELECT *,approved_applications::numeric/nullif(submitted_applications,0) AS approval_ratio,
 funded_applications::numeric/nullif(approved_applications,0) AS approved_to_funded_ratio FROM counts;
