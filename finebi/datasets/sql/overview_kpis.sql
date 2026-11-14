-- Dataset: Overview KPIs
-- Page: Portfolio Overview
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH k AS (-- Portfolio Overview: stocks at p_as_of, flows from its month start.
WITH scoped AS (
 SELECT * FROM credit.v_snapshot WHERE snapshot_date IN
 ((SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date),(date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
), current_state AS (
 SELECT coalesce(sum(principal_balance),0) AS portfolio_balance,
 count(*) FILTER(WHERE principal_balance>0) AS active_loans,
 count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) AS active_borrowers,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0) AS exposure_31_plus,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0) AS exposure_91_plus,
 coalesce(sum(overdue_principal),0) AS overdue_principal,
 coalesce(sum(overdue_interest),0) AS overdue_interest
 FROM scoped WHERE snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
), previous_state AS (
 SELECT coalesce(sum(principal_balance),0) AS previous_balance FROM scoped
 WHERE snapshot_date=(date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date
), flows AS (
 SELECT coalesce(sum(original_principal),0) AS month_to_date_disbursements
 FROM credit.v_loan_dimension WHERE issue_date BETWEEN date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
)
SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,c.*,p.previous_balance,
 c.portfolio_balance-p.previous_balance AS balance_change,
 (c.portfolio_balance-p.previous_balance)/nullif(p.previous_balance,0) AS balance_change_ratio,
 c.exposure_31_plus/nullif(c.portfolio_balance,0) AS dpd_31_plus_ratio,
 c.exposure_91_plus/nullif(c.portfolio_balance,0) AS dpd_91_plus_ratio,
 f.month_to_date_disbursements
FROM current_state c CROSS JOIN previous_state p CROSS JOIN flows f) SELECT k.*,
    CASE WHEN abs(portfolio_balance)>=1000000000 THEN 'RUB '||to_char(portfolio_balance/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(portfolio_balance/1000000,'FM999,990.00')||' m' END AS portfolio_label,CASE WHEN abs(month_to_date_disbursements)>=1000000000 THEN 'RUB '||to_char(month_to_date_disbursements/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(month_to_date_disbursements/1000000,'FM999,990.00')||' m' END AS funding_label,
    to_char(active_borrowers,'FM999,999,990') AS borrowers_label,
    to_char(active_loans,'FM999,999,990')||' active loans' AS active_loans_label,
    coalesce(to_char(dpd_31_plus_ratio*100,'FM990.00')||'%','—') AS ratio_31_label,
    coalesce(to_char(dpd_91_plus_ratio*100,'FM990.00')||'%','—') AS ratio_91_label,
    coalesce(CASE WHEN balance_change_ratio>=0 THEN '+' ELSE '' END||to_char(balance_change_ratio*100,'FM990.00')||'%','—') AS growth_label,
    CASE WHEN abs(balance_change)>=1000000000 THEN 'RUB '||to_char(balance_change/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(balance_change/1000000,'FM999,990.00')||' m' END||' change' AS growth_amount_label,
    CASE WHEN abs(exposure_31_plus)>=1000000000 THEN 'RUB '||to_char(exposure_31_plus/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(exposure_31_plus/1000000,'FM999,990.00')||' m' END||' exposure' AS exposure_31_label,CASE WHEN abs(exposure_91_plus)>=1000000000 THEN 'RUB '||to_char(exposure_91_plus/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(exposure_91_plus/1000000,'FM999,990.00')||' m' END||' exposure' AS exposure_91_label,
    CASE WHEN active_loans=0 THEN 'No loans match the selected filters.' ELSE
    'End-of-day principal balances · Full-loan exposure by days past due' END AS scope_note,
    coalesce(to_char(as_of_date,'DD Mon YYYY'),'No reporting date') AS date_label,
    coalesce(to_char(as_of_date,'FMMonth YYYY'),'No reporting date')||' funding' AS funding_note,
    'vs '||to_char(date_trunc('month',as_of_date)-interval '1 day','DD Mon YYYY') AS comparison_note
    FROM k
