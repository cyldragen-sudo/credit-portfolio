-- Dataset: Filter - Channel
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct

SELECT 0 id,'All Channels' label UNION ALL SELECT channel_id,channel_name FROM credit.channel ORDER BY id
