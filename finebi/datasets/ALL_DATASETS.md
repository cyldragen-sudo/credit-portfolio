# Credit Portfolio Analytics - All SQL Queries

One block per FineBI SQL dataset. See README.md for parameter types, defaults and field units.

## Filter - As Of Month

Page: Shared Filters

```sql
-- Dataset: Filter - As Of Month
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT to_char(calendar_date,'YYYYMMDD')::integer AS id,to_char(calendar_date,'FMMonth YYYY') label FROM credit.calendar CROSS JOIN credit.dataset_run WHERE calendar_date=month_end AND calendar_date BETWEEN report_start AND as_of_date ORDER BY calendar_date DESC
```

## Filter - Product

Page: Shared Filters

```sql
-- Dataset: Filter - Product
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT 0 id,'All Products' label UNION ALL SELECT product_id,product_name FROM credit.product ORDER BY id
```

## Filter - Region

Page: Shared Filters

```sql
-- Dataset: Filter - Region
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT 0 id,'All Regions' label UNION ALL SELECT region_id,region_name FROM credit.region ORDER BY id
```

## Filter - Channel

Page: Shared Filters

```sql
-- Dataset: Filter - Channel
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT 0 id,'All Channels' label UNION ALL SELECT channel_id,channel_name FROM credit.channel ORDER BY id
```

## Filter - Minimum DPD

Page: Shared Filters

```sql
-- Dataset: Filter - Minimum DPD
-- Page: Shared Filters
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: None

SELECT * FROM (VALUES (0,'All active'),(1,'1+ DPD'),(31,'31+ DPD'),(91,'91+ DPD')) options(id,label) ORDER BY id
```

## Overview KPIs

Page: Portfolio Overview

```sql
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
```

## Portfolio Balance Trend

Page: Portfolio Overview

```sql
-- Dataset: Portfolio Balance Trend
-- Page: Portfolio Overview
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

SELECT snapshot_date AS sort_date,to_char(snapshot_date,'Mon YY') label,'Portfolio'::text series,portfolio_balance/1000000000 AS value FROM (SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '2024-11-01'::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
GROUP BY snapshot_date ORDER BY snapshot_date) t ORDER BY snapshot_date
```

## Delinquency Trend

Page: Portfolio Overview

```sql
-- Dataset: Delinquency Trend
-- Page: Portfolio Overview
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

SELECT snapshot_date AS sort_date,to_char(snapshot_date,'Mon YY') label,'31+ DPD'::text series,dpd_31_plus_ratio*100 AS value FROM (SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '2024-11-01'::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
GROUP BY snapshot_date ORDER BY snapshot_date) t UNION ALL SELECT snapshot_date,to_char(snapshot_date,'Mon YY'),'91+ DPD',dpd_91_plus_ratio*100 FROM (SELECT snapshot_date,sum(principal_balance) AS portfolio_balance,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) AS dpd_31_plus_ratio,
 coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) AS dpd_91_plus_ratio
FROM credit.v_month_end_snapshot
WHERE snapshot_date BETWEEN '2024-11-01'::date AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
 AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
 AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
 AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})
GROUP BY snapshot_date ORDER BY snapshot_date) t ORDER BY sort_date,series
```

## Portfolio Product Composition

Page: Portfolio Overview

```sql
-- Dataset: Portfolio Product Composition
-- Page: Portfolio Overview
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

SELECT product_name label,'Principal balance'::text series,sum(principal_balance)/1000000000 AS value FROM credit.v_snapshot WHERE snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
      AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
      AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)}) AND principal_balance>0 GROUP BY product_name ORDER BY value DESC
```

## Regional Performance

Page: Portfolio Overview

```sql
-- Dataset: Regional Performance
-- Page: Portfolio Overview
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH states AS (SELECT * FROM credit.v_snapshot WHERE snapshot_date IN ((SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date),
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date) AND (${INT(p_product_id)}=0 OR product_id=${INT(p_product_id)})
      AND (${INT(p_channel_id)}=0 OR channel_id=${INT(p_channel_id)})
      AND (${INT(p_region_id)}=0 OR region_id=${INT(p_region_id)})),
      current_state AS (SELECT region_id,region_name,sum(principal_balance) balance,
        count(DISTINCT customer_id) FILTER(WHERE principal_balance>0) borrowers,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=31),0)/nullif(sum(principal_balance),0) ratio31,
        coalesce(sum(principal_balance) FILTER(WHERE dpd>=91),0)/nullif(sum(principal_balance),0) ratio91
        FROM states WHERE snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2),
      previous_state AS (SELECT region_id,sum(principal_balance) balance FROM states
        WHERE snapshot_date=(date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date GROUP BY 1)
      SELECT c.region_id,c.region_name,c.balance,c.borrowers,c.ratio31,c.ratio91,
      to_char(c.balance/1000000000,'FM990.00') AS balance_label,
      coalesce(CASE WHEN c.balance>=p.balance THEN '+' ELSE '' END||to_char((c.balance-p.balance)/nullif(p.balance,0)*100,'FM990.00')||'%','—') AS growth_label,
      to_char(c.borrowers,'FM999,990') AS borrowers_label,
      coalesce(to_char(c.ratio31*100,'FM990.00')||'%','—') AS ratio31_label,
      coalesce(to_char(c.ratio91*100,'FM990.00')||'%','—') AS ratio91_label
      FROM current_state c LEFT JOIN previous_state p USING(region_id) ORDER BY c.balance DESC,c.region_id
```

## Sales KPIs

Page: Sales and Funnel

```sql
-- Dataset: Sales KPIs
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})), cohort_counts AS (SELECT count(*) AS submitted_applications,
      count(*) FILTER(WHERE approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE funded_date<=d.as_of_date) AS cohort_funded_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Declined') AS declined_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Withdrawn') AS withdrawn_applications,
      count(*) FILTER(WHERE (funded_date IS NULL OR funded_date>d.as_of_date)
        AND (terminal_date IS NULL OR terminal_date>d.as_of_date)) AS in_progress_applications,
      avg(funded_date-submitted_date) FILTER(WHERE funded_date<=d.as_of_date) AS average_days_to_funding
      FROM cohort CROSS JOIN bounds d),
    flow_counts AS (SELECT count(*) AS funded_loans,coalesce(sum(original_principal),0) AS funded_amount,
      avg(original_principal) AS average_funded_amount FROM funded),
    k AS (SELECT c.*,f.*,d.*,c.approved_applications::numeric/nullif(c.submitted_applications,0) AS approval_ratio,
      c.cohort_funded_applications::numeric/nullif(c.approved_applications,0) AS approved_to_funded_ratio
      FROM cohort_counts c CROSS JOIN flow_counts f CROSS JOIN bounds d) SELECT k.*,
      CASE WHEN abs(funded_amount)>=1000000000 THEN 'RUB '||to_char(funded_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(funded_amount/1000000,'FM999,990.00')||' m' END AS funded_amount_label,
      to_char(funded_loans,'FM999,999,990') AS funded_loans_label,
      coalesce(CASE WHEN abs(average_funded_amount)>=1000000000 THEN 'RUB '||to_char(average_funded_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(average_funded_amount/1000000,'FM999,990.00')||' m' END,'—') AS average_amount_label,
      to_char(submitted_applications,'FM999,999,990') AS applications_label,
      coalesce(to_char(approval_ratio*100,'FM990.00')||'%','—') AS approval_label,
      coalesce(to_char(approved_to_funded_ratio*100,'FM990.00')||'%','—') AS conversion_label,
      to_char(approved_applications,'FM999,999,990')||' approved applications' AS approval_note,
      to_char(cohort_funded_applications,'FM999,999,990')||' funded from submission cohort' AS conversion_note,
      coalesce(to_char(as_of_date,'DD Mon YYYY'),'No reporting date') AS date_label,
      coalesce(to_char(as_of_date,'FMMonth YYYY'),'No reporting date') AS month_label,
      'Declined: '||declined_applications||'   ·   Withdrawn: '||withdrawn_applications||'   ·   In progress: '||in_progress_applications AS funnel_summary,
      'Avg time to funding: '||coalesce(to_char(average_days_to_funding,'FM990.0')||' days','—') AS funding_time_label,
      'Submitted in '||to_char(as_of_date,'Mon YYYY')||' · Outcomes through '||to_char(as_of_date,'DD Mon YYYY') AS cohort_note,
      CASE WHEN submitted_applications=0 AND funded_loans=0 THEN 'No sales or applications match the selected filters.'
      ELSE 'Submission cohorts and funded-date sales are separate populations. Recent applications may still be in progress.' END AS scope_note
      FROM k
```

## Application Funnel

Page: Sales and Funnel

```sql
-- Dataset: Application Funnel
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})), cohort_counts AS (SELECT count(*) AS submitted_applications,
      count(*) FILTER(WHERE approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE funded_date<=d.as_of_date) AS cohort_funded_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Declined') AS declined_applications,
      count(*) FILTER(WHERE terminal_date<=d.as_of_date AND outcome='Withdrawn') AS withdrawn_applications,
      count(*) FILTER(WHERE (funded_date IS NULL OR funded_date>d.as_of_date)
        AND (terminal_date IS NULL OR terminal_date>d.as_of_date)) AS in_progress_applications,
      avg(funded_date-submitted_date) FILTER(WHERE funded_date<=d.as_of_date) AS average_days_to_funding
      FROM cohort CROSS JOIN bounds d),
    flow_counts AS (SELECT count(*) AS funded_loans,coalesce(sum(original_principal),0) AS funded_amount,
      avg(original_principal) AS average_funded_amount FROM funded),
    k AS (SELECT c.*,f.*,d.*,c.approved_applications::numeric/nullif(c.submitted_applications,0) AS approval_ratio,
      c.cohort_funded_applications::numeric/nullif(c.approved_applications,0) AS approved_to_funded_ratio
      FROM cohort_counts c CROSS JOIN flow_counts f CROSS JOIN bounds d) SELECT stage,label,'Applications'::text AS series,value
      FROM k CROSS JOIN LATERAL (VALUES
        (1,'Submitted',submitted_applications),(2,'Approved',approved_applications),
        (3,'Funded',cohort_funded_applications)) stages(stage,label,value)
      WHERE submitted_applications>0 ORDER BY stage
```

## Disbursement Trend

Page: Sales and Funnel

```sql
-- Dataset: Disbursement Trend
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date),loans AS (
      SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN '2024-11-01'::date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})),
      monthly AS (SELECT date_trunc('month',issue_date)::date month_start,sum(original_principal) amount FROM loans GROUP BY 1)
      SELECT c.calendar_date AS month_end,to_char(c.calendar_date,'Mon YY') label,
      'Disbursements'::text series,coalesce(m.amount,0)/1000000 AS value
      FROM credit.calendar c CROSS JOIN bounds d LEFT JOIN monthly m ON m.month_start=c.month_start
      WHERE c.calendar_date=c.month_end AND c.calendar_date BETWEEN '2024-11-01'::date AND d.as_of_date
      AND EXISTS(SELECT 1 FROM loans) ORDER BY c.calendar_date
```

## Disbursements by Channel

Page: Sales and Funnel

```sql
-- Dataset: Disbursements by Channel
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})) SELECT channel_name AS label,'Disbursements'::text AS series,
      sum(original_principal)/1000000 AS value FROM funded GROUP BY channel_name ORDER BY value DESC
```

## Sales Plan vs Actual

Page: Sales and Funnel

```sql
-- Dataset: Sales Plan vs Actual
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS month_start),
      actual AS (SELECT l.product_id,l.branch_id,count(*) AS funded_loans,sum(l.original_principal) amount
        FROM credit.loan l CROSS JOIN bounds d WHERE l.issue_date BETWEEN d.month_start AND d.as_of_date GROUP BY 1,2)
      SELECT p.product_id,n.product_name,sum(coalesce(a.funded_loans,0)) AS funded_loans,
        sum(coalesce(a.amount,0)) AS funded_amount,sum(p.planned_amount) AS planned_amount,
        sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0) AS plan_attainment,
        to_char(sum(coalesce(a.funded_loans,0)),'FM999,990') AS loans_label,
        to_char(sum(coalesce(a.amount,0))/1000000,'FM999,990.00') AS actual_label,
        to_char(sum(p.planned_amount)/1000000,'FM999,990.00') AS plan_label,
        coalesce(to_char(sum(coalesce(a.amount,0))/nullif(sum(p.planned_amount),0)*100,'FM990.0')||'%','—') AS attainment_label
      FROM credit.sales_plan p CROSS JOIN bounds d JOIN credit.product n USING(product_id)
      JOIN credit.branch b USING(branch_id) LEFT JOIN actual a ON a.product_id=p.product_id AND a.branch_id=p.branch_id
      WHERE p.plan_month=d.month_start AND (${INT(p_product_id)}=0 OR p.product_id=${INT(p_product_id)})
      AND (${INT(p_region_id)}=0 OR b.region_id=${INT(p_region_id)})
      GROUP BY p.product_id,n.product_name ORDER BY p.product_id
```

## Channel Funnel Performance

Page: Sales and Funnel

```sql
-- Dataset: Channel Funnel Performance
-- Page: Sales and Funnel
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))::date AS start_date),
    applications AS (SELECT a.*,b.region_id FROM credit.application a JOIN credit.branch b USING(branch_id)),
    cohort AS (SELECT a.* FROM applications a CROSS JOIN bounds d
      WHERE a.submitted_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR a.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR a.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR a.channel_id=${INT(p_channel_id)})),
    funded AS (SELECT l.* FROM credit.v_loan_dimension l CROSS JOIN bounds d
      WHERE l.issue_date BETWEEN d.start_date AND d.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})) SELECT c.channel_id,n.channel_name,count(*) AS submitted_applications,
      count(*) FILTER(WHERE c.approved_date<=d.as_of_date) AS approved_applications,
      count(*) FILTER(WHERE c.funded_date<=d.as_of_date) AS cohort_funded_applications,
      to_char(count(*),'FM999,990') AS applications_label,
      coalesce(to_char(count(*) FILTER(WHERE c.approved_date<=d.as_of_date)::numeric/nullif(count(*),0)*100,'FM990.0')||'%','—') AS approval_label,
      coalesce(to_char(count(*) FILTER(WHERE c.funded_date<=d.as_of_date)::numeric/
        nullif(count(*) FILTER(WHERE c.approved_date<=d.as_of_date),0)*100,'FM990.0')||'%','—') AS conversion_label,
      coalesce(to_char(avg(c.funded_date-c.submitted_date) FILTER(WHERE c.funded_date<=d.as_of_date),'FM990.0'),'—') AS days_label
      FROM cohort c CROSS JOIN bounds d JOIN credit.channel n USING(channel_id)
      GROUP BY c.channel_id,n.channel_name ORDER BY c.channel_id
```

## Portfolio Quality KPIs

Page: Delinquency and Portfolio Quality

```sql
-- Dataset: Portfolio Quality KPIs
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number), p_min_dpd = 1 (Number)

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
    registry_counts AS (SELECT count(*) AS registry_total FROM eligible), summary AS (
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
      FROM summary s CROSS JOIN registry_counts p CROSS JOIN bounds b CROSS JOIN writeoffs w)
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
      CASE WHEN registry_total=0 THEN 'No loans meet the registry threshold.'
        ELSE 'Ordered by DPD, principal balance and loan ID · amounts in RUB' END AS registry_note,
      CASE WHEN active_loans=0 THEN 'No active loans match the selected filters.'
        ELSE 'Full-loan exposure includes overdue principal. Registry threshold affects the loan list only.' END AS scope_note
    FROM k
```

## DPD Bucket Exposure

Page: Delinquency and Portfolio Quality

```sql
-- Dataset: DPD Bucket Exposure
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

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
      WHERE s.snapshot_date=b.as_of_date AND (${INT(p_product_id)}=0 OR s.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR s.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR s.channel_id=${INT(p_channel_id)})), states(ord,label) AS (VALUES (0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+')),
      grouped AS (SELECT dpd_bucket,count(*) AS active_loans,sum(principal_balance) balance
        FROM current_rows WHERE principal_balance>0 GROUP BY dpd_bucket)
      SELECT s.label,'Principal exposure'::text AS series,coalesce(g.balance,0)/1000000000 AS value,
        coalesce(g.active_loans,0) AS active_loans
      FROM states s LEFT JOIN grouped g ON g.dpd_bucket=s.label
      WHERE EXISTS(SELECT 1 FROM current_rows WHERE principal_balance>0) ORDER BY s.ord
```

## DPD Transition Matrix

Page: Delinquency and Portfolio Quality

```sql
-- Dataset: DPD Transition Matrix
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

WITH bounds AS (SELECT (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AS as_of_date,
      (date_trunc('month',(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))-interval '1 day')::date AS previous_date),
      states(ord,bucket) AS (VALUES(0,'0'),(1,'1-30'),(2,'31-60'),(3,'61-90'),(4,'91+'),(5,'Closed'),(6,'Written Off')),
      pairs AS (SELECT a.loan_id,
        CASE WHEN a.loan_status='Active' THEN a.dpd_bucket ELSE a.loan_status END AS from_bucket,
        CASE WHEN z.loan_status='Active' THEN z.dpd_bucket ELSE z.loan_status END AS to_bucket
        FROM credit.loan_snapshot a JOIN credit.loan_snapshot z USING(loan_id)
        JOIN credit.v_loan_dimension l USING(loan_id) CROSS JOIN bounds b
        WHERE a.snapshot_date=b.previous_date AND z.snapshot_date=b.as_of_date AND (${INT(p_product_id)}=0 OR l.product_id=${INT(p_product_id)}) AND (${INT(p_region_id)}=0 OR l.region_id=${INT(p_region_id)}) AND (${INT(p_channel_id)}=0 OR l.channel_id=${INT(p_channel_id)})),
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
```

## Loan Registry

Page: Delinquency and Portfolio Quality

```sql
-- Dataset: Loan Registry
-- Page: Delinquency and Portfolio Quality
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number), p_min_dpd = 1 (Number)

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
    ordered AS (SELECT *,row_number() OVER(
      ORDER BY dpd DESC,principal_balance DESC,loan_id) AS registry_row_no FROM eligible)
      SELECT e.snapshot_date,e.loan_id,e.loan_reference,e.customer_label,e.product_name,e.region_name,e.channel_name,
        e.principal_balance,e.overdue_principal,e.overdue_interest,e.dpd,e.dpd_bucket,
        to_char(e.principal_balance,'FM999,999,990.00') AS balance_label,
        to_char(e.overdue_principal,'FM999,999,990.00') AS overdue_principal_label,
        to_char(e.overdue_interest,'FM999,999,990.00') AS overdue_interest_label,
        e.dpd::text AS dpd_label,e.registry_row_no
      FROM ordered e
      ORDER BY e.registry_row_no
```

## Vintage KPIs

Page: Vintage Analysis

```sql
-- Dataset: Vintage KPIs
-- Page: Vintage Analysis
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

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
sum(ever_count) FILTER(WHERE mob=12 AND observation_status='Observed')::numeric/nullif(sum(original_loan_count) FILTER(WHERE mob=12 AND observation_status='Observed'),0) AS mob12_ratio FROM measured)
      SELECT t.*,r.*,b.as_of_date,to_char(b.as_of_date,'DD Mon YYYY') date_label,
        to_char(t.original_loans,'FM999,990') original_loans_label,
        CASE WHEN abs(t.original_amount)>=1000000000 THEN 'RUB '||to_char(t.original_amount/1000000000,'FM999,990.00')||' bn' ELSE 'RUB '||to_char(t.original_amount/1000000,'FM999,990.00')||' m' END original_amount_label,t.cohort_count::text cohort_count_label,
        to_char(b.report_start,'Mon YYYY')||' – '||to_char(b.as_of_date,'Mon YYYY') cohort_window_label,
        CASE WHEN t.original_loans=0 THEN 'No origination cohorts match the selected filters.'
          ELSE 'Original contract counts · Closed and written-off loans remain in the denominator.' END scope_note,
        coalesce(to_char(mob3_ratio*100,'FM990.00')||'%','—') mob3_label, mob3_cohorts||' mature cohorts · '||to_char(mob3_loans,'FM999,990')||' loans' mob3_note,
coalesce(to_char(mob6_ratio*100,'FM990.00')||'%','—') mob6_label, mob6_cohorts||' mature cohorts · '||to_char(mob6_loans,'FM999,990')||' loans' mob6_note,
coalesce(to_char(mob12_ratio*100,'FM990.00')||'%','—') mob12_label, mob12_cohorts||' mature cohorts · '||to_char(mob12_loans,'FM999,990')||' loans' mob12_note
      FROM totals t CROSS JOIN rates r CROSS JOIN bounds b
```

## Vintage Matrix

Page: Vintage Analysis

```sql
-- Dataset: Vintage Matrix
-- Page: Vintage Analysis
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

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
        FROM cells) SELECT cohort_month,cohort_row,mob,original_loan_count,original_amount,maturity_date,
      observation_status,ever_count,ever_ratio,to_char(cohort_month,'Mon YY') cohort_label,
      to_char(original_loan_count,'FM999,990') count_label,
      CASE WHEN observation_status='Observed' THEN to_char(ever_ratio*100,'FM990.0')||'%' ELSE '—' END cell_label
      FROM measured ORDER BY cohort_row,mob
```

## Vintage Curves

Page: Vintage Analysis

```sql
-- Dataset: Vintage Curves
-- Page: Vintage Analysis
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_product_id = 0 (Number), p_region_id = 0 (Number), p_channel_id = 0 (Number)

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
        FROM cells) SELECT cohort_month,mob,'M'||mob label,to_char(cohort_month,'Mon YY') series,
      ever_ratio*100 value,original_loan_count,ever_count
      FROM measured WHERE observation_status='Observed' AND (curve_order-1)%6=0 AND curve_order<=19
      ORDER BY mob,cohort_month
```

## Loan Details KPIs

Page: Loan Details

```sql
-- Dataset: Loan Details KPIs
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)),
      operations AS (SELECT o.* FROM (SELECT operation_id,operation_date,operation_type,principal_amount,interest_amount,
 CASE WHEN operation_type IN ('REPAYMENT','PREPAYMENT') THEN principal_amount+interest_amount
 ELSE 0 END AS cash_received
FROM credit.loan_operation WHERE loan_id=${INT(p_loan_id)} AND operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
ORDER BY operation_date,operation_id) o WHERE EXISTS(SELECT 1 FROM selected)),
      schedule AS (SELECT s.*,s.principal_paid+s.interest_paid paid_amount,
        s.principal_written_off+s.interest_written_off written_off_amount
        FROM (WITH allocations AS (
 SELECT a.loan_id,a.schedule_version,a.installment_no,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type<>'WRITE_OFF'),0) AS principal_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type<>'WRITE_OFF'),0) AS interest_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type='WRITE_OFF'),0) AS principal_written_off,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type='WRITE_OFF'),0) AS interest_written_off
 FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
 WHERE a.loan_id=${INT(p_loan_id)} AND o.operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2,3
)
SELECT s.installment_no,s.due_date,s.principal_due,s.interest_due,
 coalesce(a.principal_paid,0) AS principal_paid,coalesce(a.interest_paid,0) AS interest_paid,
 coalesce(a.principal_written_off,0) AS principal_written_off,
 coalesce(a.interest_written_off,0) AS interest_written_off,
 CASE WHEN s.cancelled_on<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.cancelled_on END AS cancelled_on,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.principal_due-coalesce(a.principal_paid,0)-coalesce(a.principal_written_off,0) ELSE 0 END AS overdue_principal,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (s.cancelled_on IS NULL OR s.cancelled_on>(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))
 THEN s.interest_due-coalesce(a.interest_paid,0)-coalesce(a.interest_written_off,0) ELSE 0 END AS overdue_interest
FROM credit.payment_schedule s LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
WHERE s.loan_id=${INT(p_loan_id)} AND s.effective_from<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) ORDER BY s.installment_no) s WHERE EXISTS(SELECT 1 FROM selected)),
      counts AS (SELECT (SELECT count(*) FROM operations) operation_count,
        (SELECT count(*) FROM schedule) schedule_count) SELECT h.*,p.*,coalesce(h.loan_id,0) selected_loan_id,(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) as_of_date,to_char((SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date),'DD Mon YYYY') date_label,CASE WHEN h.loan_id IS NULL THEN 'No loan selected' ELSE h.loan_reference||' · '||h.customer_label||' · '||h.product_name END identity_label,CASE WHEN h.loan_id IS NULL THEN CASE WHEN ${INT(p_loan_id)}=0 THEN 'Open a loan from Portfolio Quality to view its details.' ELSE 'This loan is not available as of the selected date.' END ELSE 'Contract follows loan ID and As of; portfolio filters are retained for return.' END scope_note,CASE WHEN h.loan_id IS NULL THEN '—' ELSE h.dpd::text END dpd_label,coalesce(h.loan_status,'—') status_label,coalesce(to_char(h.issue_date,'DD Mon YYYY'),'—') issue_label,coalesce(to_char(h.maturity_date,'DD Mon YYYY'),'—') maturity_label,coalesce(to_char(h.actual_close_date,'DD Mon YYYY'),'—') close_label,coalesce(to_char(h.annual_rate,'FM990.00')||'%','—') rate_label,coalesce(h.term_months||' months','—') term_label,coalesce(h.region_name||' · '||h.branch_name||' · '||h.channel_name||' · Origination risk: '||h.risk_at_origination,'Select a contract in the loan registry.') origination_label,coalesce((SELECT sum(cash_received) FROM operations),0) cash_received,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.principal_balance,'FM999,999,999,990.00') END balance_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.overdue_principal,'FM999,999,999,990.00') END overdue_principal_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.overdue_interest,'FM999,999,999,990.00') END overdue_interest_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(h.original_principal,'FM999,999,999,990.00') END original_label,CASE WHEN h.loan_id IS NULL THEN '—' ELSE 'RUB '||to_char(coalesce((SELECT sum(cash_received) FROM operations),0),'FM999,999,999,990.00') END cash_label FROM counts p LEFT JOIN selected h ON true
```

## Loan Balance History

Page: Loan Details

```sql
-- Dataset: Loan Balance History
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)) SELECT s.snapshot_date,to_char(s.snapshot_date,'Mon YY') label,
      'Principal balance'::text series,s.principal_balance/1000000 value FROM credit.loan_snapshot s JOIN credit.calendar c ON c.calendar_date=s.snapshot_date
      CROSS JOIN credit.dataset_run d WHERE s.loan_id=${INT(p_loan_id)} AND EXISTS(SELECT 1 FROM selected)
      AND s.snapshot_date BETWEEN d.report_start AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND s.snapshot_date=c.month_end ORDER BY s.snapshot_date
```

## Loan DPD History

Page: Loan Details

```sql
-- Dataset: Loan DPD History
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)) SELECT s.snapshot_date,to_char(s.snapshot_date,'Mon YY') label,
      'DPD'::text series,s.dpd value FROM credit.loan_snapshot s JOIN credit.calendar c ON c.calendar_date=s.snapshot_date
      CROSS JOIN credit.dataset_run d WHERE s.loan_id=${INT(p_loan_id)} AND EXISTS(SELECT 1 FROM selected)
      AND s.snapshot_date BETWEEN d.report_start AND (SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND s.snapshot_date=c.month_end ORDER BY s.snapshot_date
```

## Loan Operations

Page: Loan Details

```sql
-- Dataset: Loan Operations
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)),
      operations AS (SELECT o.* FROM (SELECT operation_id,operation_date,operation_type,principal_amount,interest_amount,
 CASE WHEN operation_type IN ('REPAYMENT','PREPAYMENT') THEN principal_amount+interest_amount
 ELSE 0 END AS cash_received
FROM credit.loan_operation WHERE loan_id=${INT(p_loan_id)} AND operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
ORDER BY operation_date,operation_id) o WHERE EXISTS(SELECT 1 FROM selected)),
      schedule AS (SELECT s.*,s.principal_paid+s.interest_paid paid_amount,
        s.principal_written_off+s.interest_written_off written_off_amount
        FROM (WITH allocations AS (
 SELECT a.loan_id,a.schedule_version,a.installment_no,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type<>'WRITE_OFF'),0) AS principal_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type<>'WRITE_OFF'),0) AS interest_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type='WRITE_OFF'),0) AS principal_written_off,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type='WRITE_OFF'),0) AS interest_written_off
 FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
 WHERE a.loan_id=${INT(p_loan_id)} AND o.operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2,3
)
SELECT s.installment_no,s.due_date,s.principal_due,s.interest_due,
 coalesce(a.principal_paid,0) AS principal_paid,coalesce(a.interest_paid,0) AS interest_paid,
 coalesce(a.principal_written_off,0) AS principal_written_off,
 coalesce(a.interest_written_off,0) AS interest_written_off,
 CASE WHEN s.cancelled_on<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.cancelled_on END AS cancelled_on,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.principal_due-coalesce(a.principal_paid,0)-coalesce(a.principal_written_off,0) ELSE 0 END AS overdue_principal,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (s.cancelled_on IS NULL OR s.cancelled_on>(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))
 THEN s.interest_due-coalesce(a.interest_paid,0)-coalesce(a.interest_written_off,0) ELSE 0 END AS overdue_interest
FROM credit.payment_schedule s LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
WHERE s.loan_id=${INT(p_loan_id)} AND s.effective_from<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) ORDER BY s.installment_no) s WHERE EXISTS(SELECT 1 FROM selected)), ordered AS (SELECT *,row_number() OVER(ORDER BY operation_date DESC,operation_id DESC) row_no FROM operations)
      SELECT o.*,to_char(operation_date,'DD Mon YY') date_label,
        initcap(replace(operation_type,'_',' ')) type_label,
        to_char(principal_amount,'FM999,999,990.00') principal_label,
        to_char(interest_amount,'FM999,999,990.00') interest_label,
        to_char(cash_received,'FM999,999,990.00') cash_label
      FROM ordered o ORDER BY row_no
```

## Loan Payment Schedule

Page: Loan Details

```sql
-- Dataset: Loan Payment Schedule
-- Page: Loan Details
-- Connection: CREDIT_PORTFOLIO | Mode: Direct
-- Parameters: p_date_key = 20261031 (Number), p_loan_id = 0 (Number)

WITH selected AS (SELECT l.loan_id,l.loan_reference,l.customer_label,l.product_name,l.channel_name,l.branch_name,
 l.region_name,l.issue_date,l.original_principal,l.annual_rate,l.term_months,l.maturity_date,
 l.currency,l.risk_at_origination,s.snapshot_date,s.principal_balance,s.overdue_principal,
 s.overdue_interest,s.dpd,s.dpd_bucket,s.loan_status,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.actual_close_date END AS actual_close_date,
 CASE WHEN l.actual_close_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN l.close_reason END AS close_reason
FROM credit.v_loan_dimension l JOIN credit.loan_snapshot s USING(loan_id)
WHERE l.loan_id=${INT(p_loan_id)} AND s.snapshot_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)),
      operations AS (SELECT o.* FROM (SELECT operation_id,operation_date,operation_type,principal_amount,interest_amount,
 CASE WHEN operation_type IN ('REPAYMENT','PREPAYMENT') THEN principal_amount+interest_amount
 ELSE 0 END AS cash_received
FROM credit.loan_operation WHERE loan_id=${INT(p_loan_id)} AND operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date)
ORDER BY operation_date,operation_id) o WHERE EXISTS(SELECT 1 FROM selected)),
      schedule AS (SELECT s.*,s.principal_paid+s.interest_paid paid_amount,
        s.principal_written_off+s.interest_written_off written_off_amount
        FROM (WITH allocations AS (
 SELECT a.loan_id,a.schedule_version,a.installment_no,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type<>'WRITE_OFF'),0) AS principal_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type<>'WRITE_OFF'),0) AS interest_paid,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Principal' AND operation_type='WRITE_OFF'),0) AS principal_written_off,
 coalesce(sum(allocated_amount) FILTER(WHERE component='Interest' AND operation_type='WRITE_OFF'),0) AS interest_written_off
 FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
 WHERE a.loan_id=${INT(p_loan_id)} AND o.operation_date<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) GROUP BY 1,2,3
)
SELECT s.installment_no,s.due_date,s.principal_due,s.interest_due,
 coalesce(a.principal_paid,0) AS principal_paid,coalesce(a.interest_paid,0) AS interest_paid,
 coalesce(a.principal_written_off,0) AS principal_written_off,
 coalesce(a.interest_written_off,0) AS interest_written_off,
 CASE WHEN s.cancelled_on<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.cancelled_on END AS cancelled_on,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN s.principal_due-coalesce(a.principal_paid,0)-coalesce(a.principal_written_off,0) ELSE 0 END AS overdue_principal,
 CASE WHEN s.due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) AND (s.cancelled_on IS NULL OR s.cancelled_on>(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date))
 THEN s.interest_due-coalesce(a.interest_paid,0)-coalesce(a.interest_written_off,0) ELSE 0 END AS overdue_interest
FROM credit.payment_schedule s LEFT JOIN allocations a USING(loan_id,schedule_version,installment_no)
WHERE s.loan_id=${INT(p_loan_id)} AND s.effective_from<=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) ORDER BY s.installment_no) s WHERE EXISTS(SELECT 1 FROM selected)), ordered AS (SELECT *,row_number() OVER(ORDER BY installment_no) row_no FROM schedule)
      SELECT s.*,installment_no::text installment_label,to_char(due_date,'DD Mon YY') date_label,
        to_char(principal_due,'FM999,999,990.00') principal_label,
        to_char(interest_due,'FM999,999,990.00') interest_label,
        to_char(paid_amount,'FM999,999,990.00') paid_label,
        to_char(written_off_amount,'FM999,999,990.00') writeoff_label,
        CASE WHEN cancelled_on IS NOT NULL THEN 'Cancelled'
          WHEN principal_paid+principal_written_off>=principal_due AND interest_paid+interest_written_off>=interest_due THEN 'Settled'
          WHEN due_date<(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN 'Overdue' WHEN due_date=(SELECT calendar_date FROM credit.calendar CROSS JOIN credit.dataset_run
 WHERE calendar_date=month_end AND to_char(calendar_date,'YYYYMMDD')::integer=${INT(p_date_key)}
 AND calendar_date BETWEEN report_start AND as_of_date) THEN 'Due today' ELSE 'Scheduled' END status_label
      FROM ordered s ORDER BY row_no
```
