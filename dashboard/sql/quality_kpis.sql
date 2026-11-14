WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date AS previous_date,
      date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS month_start),
    current_rows AS (SELECT s.* FROM credit.v_snapshot s CROSS JOIN bounds b
      WHERE s.snapshot_date=b.as_of_date AND (${INT(p_product_id)}=0 OR s.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR s.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR s.channel_id=${INT(p_channel_id)})), eligible AS (SELECT * FROM current_rows WHERE principal_balance>0
      AND loan_status='Active' AND dpd>=greatest(${INT(p_min_dpd)},0)),
    registry_counts AS (SELECT count(*) AS registry_total,
      greatest(1,ceil(count(*)::numeric/8))::integer AS registry_page_count FROM eligible),
    paging AS (SELECT *,least(greatest(${INT(p_quality_page)},1),registry_page_count)::integer AS registry_page_no
      FROM registry_counts), summary AS (
      SELECT coalesce(sum(principal_balance),0) AS portfolio_balance,
        coalesce(sum(overdue_principal),0) AS overdue_principal,
        coalesce(sum(overdue_interest),0) AS overdue_interest,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0) AS exposure_31_plus,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0) AS exposure_91_plus,
        count(*) FILTER(WHERE principal_balance>0) AS active_loans,
        count(*) FILTER(WHERE principal_balance>0 AND dpd>0) AS past_due_loans
      FROM current_rows),
    writeoffs AS (SELECT coalesce(sum(o.principal_amount),0) AS monthly_writeoffs
      FROM credit.loan_operation o JOIN credit.v_loan_dimension l USING(loan_id) CROSS JOIN bounds b
      WHERE o.operation_type='WRITE_OFF' AND o.operation_date BETWEEN b.month_start AND b.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})),
    k AS (SELECT s.*,p.*,b.*,w.*,
      s.exposure_31_plus/nullif(s.portfolio_balance,0) AS dpd_31_plus_ratio,
      s.exposure_91_plus/nullif(s.portfolio_balance,0) AS dpd_91_plus_ratio
      FROM summary s CROSS JOIN paging p CROSS JOIN bounds b CROSS JOIN writeoffs w)
    SELECT k.*,CASE WHEN abs(overdue_principal)>=1000000000 THEN 'RUB '||to_char(overdue_principal/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(overdue_principal/1000000,'FM999,990.00')||' m' END AS overdue_principal_label,CASE WHEN abs(overdue_interest)>=1000000000 THEN 'RUB '||to_char(overdue_interest/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(overdue_interest/1000000,'FM999,990.00')||' m' END AS overdue_interest_label,
      CASE WHEN abs(monthly_writeoffs)>=1000000000 THEN 'RUB '||to_char(monthly_writeoffs/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(monthly_writeoffs/1000000,'FM999,990.00')||' m' END AS writeoff_label,CASE WHEN abs(exposure_31_plus)>=1000000000 THEN 'RUB '||to_char(exposure_31_plus/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(exposure_31_plus/1000000,'FM999,990.00')||' m' END||' full-loan exposure' AS exposure31_note,
      CASE WHEN abs(exposure_91_plus)>=1000000000 THEN 'RUB '||to_char(exposure_91_plus/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(exposure_91_plus/1000000,'FM999,990.00')||' m' END||' full-loan exposure' AS exposure91_note,
      coalesce(to_char(dpd_31_plus_ratio*100,'FM990.00')||'%','—') AS ratio31_label,
      coalesce(to_char(dpd_91_plus_ratio*100,'FM990.00')||'%','—') AS ratio91_label,
      to_char(past_due_loans,'FM999,990') AS past_due_loans_label,
      to_char(active_loans,'FM999,990')||' active contracts in scope' AS active_loans_note,
      to_char(as_of_date,'DD Mon YYYY') AS date_label,
      to_char(month_start,'Mon YYYY')||' · principal written off' AS writeoff_note,
      to_char(previous_date,'DD Mon YYYY')||' → '||to_char(as_of_date,'DD Mon YYYY')||' · Opening cohort · % and count' AS transition_note,
      'Page '||registry_page_no||' of '||registry_page_count||'   ·   '||to_char(registry_total,'FM999,990')||' loans' AS registry_page_label,
      greatest(1,registry_page_no-1) AS registry_prev_page,
      least(registry_page_count,registry_page_no+1) AS registry_next_page,
      CASE WHEN registry_total=0 THEN 'No loans meet the registry threshold.'
        ELSE 'Ordered by DPD, principal balance and loan ID · amounts in RUB' END AS registry_note,
      CASE WHEN active_loans=0 THEN 'No active loans match the selected filters.'
        ELSE 'Full-loan exposure includes overdue principal. Registry threshold affects the loan list only.' END AS scope_note
    FROM k;
