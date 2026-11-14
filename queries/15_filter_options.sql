SELECT 'Product' AS filter_type,0 AS option_id,'All Products' AS option_label
UNION ALL SELECT 'Product',product_id,product_name FROM credit.product
UNION ALL SELECT 'Channel',0,'All Channels'
UNION ALL SELECT 'Channel',channel_id,channel_name FROM credit.channel
UNION ALL SELECT 'Region',0,'All Regions'
UNION ALL SELECT 'Region',region_id,region_name FROM credit.region
ORDER BY 1,2;
