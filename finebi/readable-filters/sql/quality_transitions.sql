-- Dataset: DPD Transition Matrix
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = October 2026 (Text), p_product_id = All Products (Text), p_region_id = All Regions (Text), p_channel_id = All Channels (Text)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${IF(p_date_key="October 2026",20261031,IF(p_date_key="September 2026",20260930,IF(p_date_key="August 2026",20260831,IF(p_date_key="July 2026",20260731,IF(p_date_key="June 2026",20260630,IF(p_date_key="May 2026",20260531,IF(p_date_key="April 2026",20260430,IF(p_date_key="March 2026",20260331,IF(p_date_key="February 2026",20260228,IF(p_date_key="January 2026",20260131,IF(p_date_key="December 2025",20251231,IF(p_date_key="November 2025",20251130,IF(p_date_key="October 2025",20251031,IF(p_date_key="September 2025",20250930,IF(p_date_key="August 2025",20250831,IF(p_date_key="July 2025",20250731,IF(p_date_key="June 2025",20250630,IF(p_date_key="May 2025",20250531,IF(p_date_key="April 2025",20250430,IF(p_date_key="March 2025",20250331,IF(p_date_key="February 2025",20250228,IF(p_date_key="January 2025",20250131,IF(p_date_key="December 2024",20241231,IF(p_date_key="November 2024",20241130,INT(p_date_key)))))))))))))))))))))))))}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${IF(p_date_key="October 2026",20261031,IF(p_date_key="September 2026",20260930,IF(p_date_key="August 2026",20260831,IF(p_date_key="July 2026",20260731,IF(p_date_key="June 2026",20260630,IF(p_date_key="May 2026",20260531,IF(p_date_key="April 2026",20260430,IF(p_date_key="March 2026",20260331,IF(p_date_key="February 2026",20260228,IF(p_date_key="January 2026",20260131,IF(p_date_key="December 2025",20251231,IF(p_date_key="November 2025",20251130,IF(p_date_key="October 2025",20251031,IF(p_date_key="September 2025",20250930,IF(p_date_key="August 2025",20250831,IF(p_date_key="July 2025",20250731,IF(p_date_key="June 2025",20250630,IF(p_date_key="May 2025",20250531,IF(p_date_key="April 2025",20250430,IF(p_date_key="March 2025",20250331,IF(p_date_key="February 2025",20250228,IF(p_date_key="January 2025",20250131,IF(p_date_key="December 2024",20241231,IF(p_date_key="November 2024",20241130,INT(p_date_key)))))))))))))))))))))))))}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date AS previous_date),
      states(ord,bucket) AS (VALUES(0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+'),(5,'Closed'),(6,'Written Off')),
      pairs AS (SELECT a.loan_id,
        CASE WHEN a.loan_status='Active' THEN a.dpd_bucket ELSE a.loan_status END AS from_bucket,
        CASE WHEN z.loan_status='Active' THEN z.dpd_bucket ELSE z.loan_status END AS to_bucket
        FROM credit.loan_snapshot a JOIN credit.loan_snapshot z USING(loan_id)
        JOIN credit.v_loan_dimension l USING(loan_id) CROSS JOIN bounds b
        WHERE a.snapshot_date=b.previous_date AND z.snapshot_date=b.as_of_date AND (${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))}=0 OR l.product_id=${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))}) AND (${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))}=0 OR l.region_id=${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))}) AND (${IF(p_channel_id="All Channels",0,IF(p_channel_id="Branch",1,IF(p_channel_id="Online",2,IF(p_channel_id="Mobile App",3,IF(p_channel_id="Partner",4,INT(p_channel_id))))))}=0 OR l.channel_id=${IF(p_channel_id="All Channels",0,IF(p_channel_id="Branch",1,IF(p_channel_id="Online",2,IF(p_channel_id="Mobile App",3,IF(p_channel_id="Partner",4,INT(p_channel_id))))))})),
      opening AS (SELECT from_bucket,count(*) AS opening_loans FROM pairs GROUP BY from_bucket),
      movement AS (SELECT from_bucket,to_bucket,count(*) AS loan_count FROM pairs GROUP BY 1,2),
      cells AS (SELECT f.ord AS from_order,t.ord AS to_order,f.bucket AS from_bucket,t.bucket AS to_bucket,
        coalesce(o.opening_loans,0) AS opening_loans,coalesce(m.loan_count,0) AS loan_count,
        coalesce(m.loan_count,0)::numeric/nullif(o.opening_loans,0) AS transition_ratio
        FROM states f CROSS JOIN states t LEFT JOIN opening o ON o.from_bucket=f.bucket
        LEFT JOIN movement m ON m.from_bucket=f.bucket AND m.to_bucket=t.bucket)
      SELECT *,from_bucket||' ('||to_char(opening_loans,'FM999,990')||')' AS row_label,
        CASE WHEN opening_loans=0 THEN '—' WHEN loan_count=0 THEN '0%'
        ELSE to_char(transition_ratio*100,'FM990.0')||'% · '||to_char(loan_count,'FM999,990') END AS cell_label
      FROM cells ORDER BY from_order,to_order
