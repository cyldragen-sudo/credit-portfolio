WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date,report_start FROM credit.dataset_run),
      loans AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds b
        WHERE l.issue_date BETWEEN b.report_start AND b.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})),
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
        FROM cells), totals AS (SELECT count(*) original_loans,coalesce(sum(original_principal),0) original_amount,
      count(DISTINCT cohort_month) cohort_count FROM loans),
      rates AS (SELECT count(*) FILTER(WHERE mob=3 AND observation_status='Observed') AS mob3_cohorts,
coalesce(sum(original_loan_count) FILTER(WHERE mob=3 AND observation_status='Observed'),0) AS mob3_loans,
sum(ever_count) FILTER(WHERE mob=3 AND observation_status='Observed')::numeric/nullif(sum(original_loan_count) FILTER(WHERE mob=3 AND observation_status='Observed'),0) AS mob3_ratio,
count(*) FILTER(WHERE mob=6 AND observation_status='Observed') AS mob6_cohorts,
coalesce(sum(original_loan_count) FILTER(WHERE mob=6 AND observation_status='Observed'),0) AS mob6_loans,
sum(ever_count) FILTER(WHERE mob=6 AND observation_status='Observed')::numeric/nullif(sum(original_loan_count) FILTER(WHERE mob=6 AND observation_status='Observed'),0) AS mob6_ratio,
count(*) FILTER(WHERE mob=12 AND observation_status='Observed') AS mob12_cohorts,
coalesce(sum(original_loan_count) FILTER(WHERE mob=12 AND observation_status='Observed'),0) AS mob12_loans,
sum(ever_count) FILTER(WHERE mob=12 AND observation_status='Observed')::numeric/nullif(sum(original_loan_count) FILTER(WHERE mob=12 AND observation_status='Observed'),0) AS mob12_ratio FROM measured),
      view_counts AS (SELECT greatest(1,ceil(cohort_count::numeric/6))::integer matrix_page_count FROM totals),
      matrix_view AS (SELECT *,least(greatest(${INT(p_vintage_page)},1),matrix_page_count)::integer matrix_page_no,
        CASE WHEN ${INT(p_vintage_mob_start)}=7 THEN 7 ELSE 1 END matrix_mob_start FROM view_counts)
      SELECT t.*,r.*,b.as_of_date,to_char(b.as_of_date,'DD Mon YYYY') date_label,
        to_char(t.original_loans,'FM999,990') original_loans_label,
        CASE WHEN abs(t.original_amount)>=1000000000 THEN 'RUB '||to_char(t.original_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(t.original_amount/1000000,'FM999,990.00')||' m' END original_amount_label,t.cohort_count::text cohort_count_label,
        to_char(b.report_start,'Mon YYYY')||' – '||to_char(b.as_of_date,'Mon YYYY') cohort_window_label,
        CASE WHEN t.original_loans=0 THEN 'No origination cohorts match the selected filters.'
          ELSE 'Original contract counts · Closed and written-off loans remain in the denominator.' END scope_note,
        coalesce(to_char(mob3_ratio*100,'FM990.00')||'%','—') mob3_label, mob3_cohorts||' mature cohorts · '||to_char(mob3_loans,'FM999,990')||' loans' mob3_note,
coalesce(to_char(mob6_ratio*100,'FM990.00')||'%','—') mob6_label, mob6_cohorts||' mature cohorts · '||to_char(mob6_loans,'FM999,990')||' loans' mob6_note,
coalesce(to_char(mob12_ratio*100,'FM990.00')||'%','—') mob12_label, mob12_cohorts||' mature cohorts · '||to_char(mob12_loans,'FM999,990')||' loans' mob12_note,p.matrix_page_count,p.matrix_page_no,p.matrix_mob_start,
        greatest(1,p.matrix_page_no-1) matrix_prev_page,
        least(p.matrix_page_count,p.matrix_page_no+1) matrix_next_page,
        CASE WHEN t.cohort_count=0 THEN 'No cohorts · Page 1 of 1'
          ELSE 'Cohorts '||((p.matrix_page_no-1)*6+1)||'–'||least(p.matrix_page_no*6,t.cohort_count)||' of '||t.cohort_count END matrix_page_label
      FROM totals t CROSS JOIN rates r CROSS JOIN bounds b CROSS JOIN matrix_view p;
