-- Dataset: Filter - As Of Month
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT to_char(calendar_date,'YYYYMMDD')::integer AS id,to_char(calendar_date,'FMMonth YYYY') label FROM credit.calendar CROSS JOIN credit.dataset_run WHERE calendar_date=month_end AND calendar_date BETWEEN report_start AND as_of_date ORDER BY calendar_date DESC
