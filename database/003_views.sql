CREATE INDEX loan_snapshot_loan_date_idx ON credit.loan_snapshot(loan_id, snapshot_date);
CREATE INDEX loan_issue_date_idx ON credit.loan(issue_date);
CREATE INDEX loan_operation_loan_date_idx ON credit.loan_operation(loan_id, operation_date);
CREATE INDEX loan_operation_date_idx ON credit.loan_operation(operation_date);
CREATE INDEX allocation_schedule_idx ON credit.payment_allocation(loan_id, schedule_version, installment_no);
CREATE INDEX application_submitted_idx ON credit.application(submitted_date);

CREATE VIEW credit.v_loan_dimension AS
SELECT l.*, p.product_name, c.channel_name, b.branch_name, b.region_id, r.region_name,
       u.customer_label, u.segment, date_trunc('month', l.issue_date)::date AS cohort_month
FROM credit.loan l JOIN credit.product p USING(product_id)
JOIN credit.channel c USING(channel_id) JOIN credit.branch b USING(branch_id)
JOIN credit.region r ON r.region_id=b.region_id JOIN credit.customer u USING(customer_id);

CREATE VIEW credit.v_snapshot AS
SELECT s.*, l.loan_reference, l.customer_id, l.customer_label, l.product_id, l.product_name,
       l.channel_id, l.channel_name, l.branch_id, l.branch_name, l.region_id, l.region_name,
       l.issue_date, l.cohort_month, l.risk_at_origination
FROM credit.loan_snapshot s JOIN credit.v_loan_dimension l USING(loan_id);

CREATE VIEW credit.v_month_end_snapshot AS
SELECT s.* FROM credit.v_snapshot s JOIN credit.calendar c ON c.calendar_date=s.snapshot_date
WHERE c.calendar_date=c.month_end;

CREATE VIEW credit.v_portfolio_monthly AS
SELECT snapshot_date, product_id, product_name, region_id, region_name,
       sum(principal_balance) AS principal_balance,
       sum(principal_balance) FILTER(WHERE dpd>=31) AS exposure_31_plus,
       sum(principal_balance) FILTER(WHERE dpd>=91) AS exposure_91_plus,
       sum(overdue_principal) AS overdue_principal, sum(overdue_interest) AS overdue_interest,
       count(*) FILTER(WHERE principal_balance>0) AS active_loans
FROM credit.v_month_end_snapshot
GROUP BY snapshot_date, product_id, product_name, region_id, region_name;

CREATE VIEW credit.v_sales_monthly AS
WITH actual AS (
    SELECT date_trunc('month', issue_date)::date AS plan_month, product_id, branch_id,
           sum(original_principal) AS funded_amount, count(*) AS funded_count
    FROM credit.loan GROUP BY 1,2,3
)
SELECT p.*, d.product_name, b.branch_name, b.region_id, r.region_name,
       coalesce(a.funded_amount,0) AS funded_amount, coalesce(a.funded_count,0) AS funded_count,
       coalesce(a.funded_amount,0)/p.planned_amount AS plan_attainment
FROM credit.sales_plan p LEFT JOIN actual a USING(plan_month,product_id,branch_id)
JOIN credit.product d USING(product_id) JOIN credit.branch b USING(branch_id)
JOIN credit.region r USING(region_id);

CREATE VIEW credit.v_monthly_transition AS
SELECT a.snapshot_date AS from_date, b.snapshot_date AS to_date,
       a.loan_id, a.product_id, a.channel_id, a.branch_id, a.region_id,
       CASE WHEN a.loan_status='Active' THEN a.dpd_bucket ELSE a.loan_status END AS from_bucket,
       CASE WHEN b.loan_status='Active' THEN b.dpd_bucket ELSE b.loan_status END AS to_bucket,
       a.principal_balance AS opening_principal, b.principal_balance AS closing_principal
FROM credit.v_month_end_snapshot a JOIN credit.loan_snapshot b ON b.loan_id=a.loan_id
AND b.snapshot_date=(date_trunc('month',a.snapshot_date)+interval '2 months - 1 day')::date;

CREATE VIEW credit.v_schedule_actual AS
SELECT s.*, coalesce(a.principal_paid,0) AS principal_paid,
       coalesce(a.interest_paid,0) AS interest_paid,
       coalesce(a.principal_written_off,0) AS principal_written_off,
       coalesce(a.interest_written_off,0) AS interest_written_off
FROM credit.payment_schedule s LEFT JOIN (
    SELECT a.loan_id,a.schedule_version,a.installment_no,
       sum(a.allocated_amount) FILTER(WHERE a.component='Principal' AND o.operation_type<>'WRITE_OFF') AS principal_paid,
       sum(a.allocated_amount) FILTER(WHERE a.component='Interest' AND o.operation_type<>'WRITE_OFF') AS interest_paid,
       sum(a.allocated_amount) FILTER(WHERE a.component='Principal' AND o.operation_type='WRITE_OFF') AS principal_written_off,
       sum(a.allocated_amount) FILTER(WHERE a.component='Interest' AND o.operation_type='WRITE_OFF') AS interest_written_off
    FROM credit.payment_allocation a JOIN credit.loan_operation o USING(operation_id)
    GROUP BY a.loan_id,a.schedule_version,a.installment_no
) a USING(loan_id,schedule_version,installment_no);

COMMENT ON VIEW credit.v_loan_dimension IS 'Origination attributes and English labels; actual close date is the final fixture state, so mask it for historical reporting.';
COMMENT ON VIEW credit.v_snapshot IS 'One loan at one end-of-day date. Principal balance includes overdue principal; never sum across dates.';
COMMENT ON VIEW credit.v_month_end_snapshot IS 'Daily loan snapshots restricted to calendar month ends, including closed and written-off loans.';
COMMENT ON VIEW credit.v_portfolio_monthly IS 'Month-end product and region aggregates. Exposure is whole-loan principal classified by DPD, not overdue installments.';
COMMENT ON VIEW credit.v_sales_monthly IS 'Synthetic monthly plans and actual funded loans at month/product/branch grain. No channel plan exists.';
COMMENT ON VIEW credit.v_monthly_transition IS 'Consecutive month-end transitions for the opening cohort, retaining Closed and Written Off outcomes. New loans are excluded.';
COMMENT ON VIEW credit.v_schedule_actual IS 'Final-fixture payment schedule reconciliation. Use date-filtered allocations for historical loan details.';

COMMENT ON COLUMN credit.loan_snapshot.dpd IS 'Days since earliest unpaid principal or interest obligation strictly before snapshot_date; due day is DPD zero.';
COMMENT ON COLUMN credit.loan_snapshot.ever_31_plus IS 'True once a loan has reached DPD >=31 on any observed end-of-day date, including before report_start.';
COMMENT ON COLUMN credit.loan_month_age.months_on_book IS 'Completed monthly anniversary relative to the original issue date, with month-end clamping.';
COMMENT ON COLUMN credit.payment_schedule.cancelled_on IS 'Future installment cancelled following observed closure; historical detail must compare this date to its as-of parameter.';
COMMENT ON COLUMN credit.loan_operation.operation_type IS 'Positive amounts. DISBURSEMENT adds principal; REPAYMENT/PREPAYMENT remove principal and receive interest; WRITE_OFF extinguishes debt without receiving cash.';

DO $$
DECLARE r record; col record;
BEGIN
  FOR r IN SELECT c.relname, c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname='credit' AND c.relkind='r' LOOP
    EXECUTE format('COMMENT ON TABLE credit.%I IS %L',r.relname,
      'Synthetic credit portfolio: '||replace(r.relname,'_',' ')||'. See docs/data-dictionary.md for grain and field meanings.');
    FOR col IN SELECT a.attname FROM pg_attribute a WHERE a.attrelid=r.oid AND a.attnum>0
               AND NOT a.attisdropped AND col_description(r.oid,a.attnum) IS NULL LOOP
      EXECUTE format('COMMENT ON COLUMN credit.%I.%I IS %L',r.relname,col.attname,
        initcap(replace(col.attname,'_',' '))||'. Synthetic data; monetary amounts are RUB.');
    END LOOP;
  END LOOP;
END $$;
