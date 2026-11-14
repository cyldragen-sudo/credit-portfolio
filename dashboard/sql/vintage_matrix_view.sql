WITH all_cells AS (WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
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
        FROM cells) SELECT cohort_month,cohort_row,mob,original_loan_count,original_amount,maturity_date,
      observation_status,ever_count,ever_ratio,to_char(cohort_month,'Mon YY') cohort_label,
      to_char(original_loan_count,'FM999,990') count_label,
      CASE WHEN observation_status='Observed' THEN to_char(ever_ratio*100,'FM990.0')||'%' ELSE '—' END cell_label
      FROM measured ORDER BY cohort_row,mob),
      view_count AS (SELECT coalesce(max(cohort_row),0) cohort_count FROM all_cells),
      view_bounds AS (SELECT least(greatest(${INT(p_vintage_page)},1),greatest(1,ceil(cohort_count::numeric/6)))::integer page_no,
        CASE WHEN ${INT(p_vintage_mob_start)}=7 THEN 7 ELSE 1 END mob_start FROM view_count)
      SELECT c.* FROM all_cells c CROSS JOIN view_bounds b
      WHERE c.cohort_row BETWEEN (b.page_no-1)*6+1 AND b.page_no*6
        AND c.mob BETWEEN b.mob_start AND b.mob_start+5 ORDER BY c.cohort_row,c.mob;
