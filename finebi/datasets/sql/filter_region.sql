-- Dataset: Filter - Region
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT 0 id,'All Regions' label UNION ALL SELECT region_id,region_name FROM credit.region ORDER BY id
