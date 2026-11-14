-- Dataset: Vintage Curves
-- Page: Vintage Analysis
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = October 2026 (Text), p_product_id = All Products (Text), p_region_id = All Regions (Text), p_channel_id = All Channels (Text)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${IF(p_date_key="October 2026",20261031,IF(p_date_key="September 2026",20260930,IF(p_date_key="August 2026",20260831,IF(p_date_key="July 2026",20260731,IF(p_date_key="June 2026",20260630,IF(p_date_key="May 2026",20260531,IF(p_date_key="April 2026",20260430,IF(p_date_key="March 2026",20260331,IF(p_date_key="February 2026",20260228,IF(p_date_key="January 2026",20260131,IF(p_date_key="December 2025",20251231,IF(p_date_key="November 2025",20251130,IF(p_date_key="October 2025",20251031,IF(p_date_key="September 2025",20250930,IF(p_date_key="August 2025",20250831,IF(p_date_key="July 2025",20250731,IF(p_date_key="June 2025",20250630,IF(p_date_key="May 2025",20250531,IF(p_date_key="April 2025",20250430,IF(p_date_key="March 2025",20250331,IF(p_date_key="February 2025",20250228,IF(p_date_key="January 2025",20250131,IF(p_date_key="December 2024",20241231,IF(p_date_key="November 2024",20241130,INT(p_date_key)))))))))))))))))))))))))}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date,report_start FROM credit.dataset_run),
      loans AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds b
        WHERE l.issue_date BETWEEN b.report_start AND b.as_of_date AND (${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))}=0 OR l.product_id=${IF(p_product_id="All Products",0,IF(p_product_id="Personal Loan",1,IF(p_product_id="Auto Loan",2,IF(p_product_id="Mortgage",3,INT(p_product_id)))))}) AND (${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))}=0 OR l.region_id=${IF(p_region_id="All Regions",0,IF(p_region_id="Moscow",1,IF(p_region_id="Saint Petersburg",2,IF(p_region_id="Tatarstan",3,IF(p_region_id="Sverdlovsk Region",4,IF(p_region_id="Krasnodar Region",5,IF(p_region_id="Novosibirsk Region",6,INT(p_region_id))))))))}) AND (${IF(p_channel_id="All Channels",0,IF(p_channel_id="Branch",1,IF(p_channel_id="Online",2,IF(p_channel_id="Mobile App",3,IF(p_channel_id="Partner",4,INT(p_channel_id))))))}=0 OR l.channel_id=${IF(p_channel_id="All Channels",0,IF(p_channel_id="Branch",1,IF(p_channel_id="Online",2,IF(p_channel_id="Mobile App",3,IF(p_channel_id="Partner",4,INT(p_channel_id))))))})),
      cohorts AS (SELECT cohort_month,count(*) original_loan_count,sum(original_principal) original_amount,
        row_number() OVER(ORDER BY cohort_month DESC)::integer cohort_row,
        row_number() OVER(ORDER BY cohort_month)::integer curve_order
        FROM loans GROUP BY cohort_month),
      ages AS (SELECT c.*,m.mob,max((l.issue_date+make_interval(months=>m.mob))::date) maturity_date,
        count(a.loan_id) observed_count,count(a.loan_id) FILTER(WHERE a.ever_31_plus) recorded_ever_count
        FROM cohorts c JOIN loans l USING(cohort_month) CROSS JOIN generate_series(1,12) m(mob)
        CROSS JOIN bounds b LEFT JOIN credit.loan_month_age a ON a.loan_id=l.loan_id
          AND a.months_on_book=m.mob AND a.observation_date<=b.as_of_date
        GROUP BY c.cohort_month,c.original_loan_count,c.original_amount,c.cohort_row,c.curve_order,m.mob),
      cells AS (SELECT a.*,
        CASE WHEN maturity_date>b.as_of_date THEN 'Immature'
          WHEN observed_count=original_loan_count THEN 'Observed' ELSE 'Unavailable' END observation_status
        FROM ages a CROSS JOIN bounds b),
      measured AS (SELECT *,CASE WHEN observation_status='Observed' THEN recorded_ever_count END ever_count,
        CASE WHEN observation_status='Observed' THEN recorded_ever_count::numeric/original_loan_count END ever_ratio
        FROM cells) SELECT cohort_month,mob,'M'||mob label,to_char(cohort_month,'Mon YY') series,
      ever_ratio*100 value,original_loan_count,ever_count
      FROM measured WHERE observation_status='Observed' AND (curve_order-1)%6=0 AND curve_order<=19
      ORDER BY mob,cohort_month
