-- Dataset: Filter - Product
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct

SELECT 0 id,'All Products' label UNION ALL SELECT product_id,product_name FROM credit.product ORDER BY id
