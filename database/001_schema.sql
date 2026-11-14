-- English, synthetic retail credit portfolio. PostgreSQL 16+.
-- CREATE SCHEMA intentionally fails if the destination is already occupied.
CREATE SCHEMA credit;
COMMENT ON SCHEMA credit IS 'Synthetic retail credit portfolio for five FineReport pages; all amounts are RUB.';

CREATE TABLE credit.dataset_run (
    run_id integer PRIMARY KEY CHECK (run_id = 1), seed integer NOT NULL,
    history_start date NOT NULL, report_start date NOT NULL, as_of_date date NOT NULL,
    loan_count integer NOT NULL CHECK (loan_count > 0), is_synthetic boolean NOT NULL CHECK (is_synthetic),
    generator_version text NOT NULL
);
CREATE TABLE credit.region (region_id integer PRIMARY KEY, region_name text NOT NULL UNIQUE);
CREATE TABLE credit.branch (
    branch_id integer PRIMARY KEY, branch_name text NOT NULL UNIQUE,
    region_id integer NOT NULL REFERENCES credit.region
);
CREATE TABLE credit.product (product_id integer PRIMARY KEY, product_name text NOT NULL UNIQUE);
CREATE TABLE credit.channel (channel_id integer PRIMARY KEY, channel_name text NOT NULL UNIQUE);
CREATE TABLE credit.calendar (
    calendar_date date PRIMARY KEY, month_start date NOT NULL,
    month_end date NOT NULL, year_number integer NOT NULL, month_number integer NOT NULL
);
CREATE TABLE credit.customer (
    customer_id integer PRIMARY KEY, customer_label text NOT NULL UNIQUE,
    segment text NOT NULL, region_id integer NOT NULL REFERENCES credit.region,
    relationship_start date NOT NULL
);
CREATE TABLE credit.application (
    application_id bigint PRIMARY KEY, customer_id integer NOT NULL REFERENCES credit.customer,
    product_id integer NOT NULL REFERENCES credit.product,
    channel_id integer NOT NULL REFERENCES credit.channel,
    branch_id integer NOT NULL REFERENCES credit.branch,
    submitted_date date NOT NULL, requested_amount numeric(18,2) NOT NULL CHECK (requested_amount > 0),
    approved_date date, funded_date date, terminal_date date,
    outcome text NOT NULL CHECK (outcome IN ('Funded','Declined','Withdrawn','Pending','Approved')),
    CHECK (approved_date IS NULL OR approved_date >= submitted_date),
    CHECK (funded_date IS NULL OR funded_date >= approved_date),
    CHECK ((outcome = 'Funded') = (funded_date IS NOT NULL))
);
CREATE TABLE credit.application_event (
    application_id bigint NOT NULL REFERENCES credit.application,
    event_date date NOT NULL, event_sequence integer NOT NULL,
    event_status text NOT NULL CHECK (event_status IN ('Submitted','Approved','Funded','Declined','Withdrawn')),
    PRIMARY KEY (application_id, event_sequence)
);
CREATE TABLE credit.loan (
    loan_id bigint PRIMARY KEY, loan_reference text NOT NULL UNIQUE,
    application_id bigint NOT NULL UNIQUE REFERENCES credit.application,
    customer_id integer NOT NULL REFERENCES credit.customer,
    product_id integer NOT NULL REFERENCES credit.product,
    channel_id integer NOT NULL REFERENCES credit.channel,
    branch_id integer NOT NULL REFERENCES credit.branch,
    issue_date date NOT NULL, original_principal numeric(18,2) NOT NULL CHECK (original_principal > 0),
    annual_rate numeric(6,3) NOT NULL CHECK (annual_rate >= 0),
    term_months integer NOT NULL CHECK (term_months > 0), maturity_date date NOT NULL,
    currency char(3) NOT NULL CHECK (currency = 'RUB'),
    risk_at_origination text NOT NULL CHECK (risk_at_origination IN ('Low','Medium','High')),
    actual_close_date date, close_reason text CHECK (close_reason IN ('Repaid','Early Settlement','Written Off')),
    CHECK (maturity_date > issue_date),
    CHECK (actual_close_date IS NULL OR actual_close_date >= issue_date),
    CHECK ((actual_close_date IS NULL) = (close_reason IS NULL))
);
CREATE TABLE credit.simulation_scenario (
    loan_id bigint PRIMARY KEY REFERENCES credit.loan, scenario_code text NOT NULL,
    scenario_description text NOT NULL
);
CREATE TABLE credit.payment_schedule (
    loan_id bigint NOT NULL REFERENCES credit.loan, schedule_version integer NOT NULL CHECK (schedule_version = 1),
    installment_no integer NOT NULL CHECK (installment_no > 0), effective_from date NOT NULL,
    due_date date NOT NULL, principal_due numeric(18,2) NOT NULL CHECK (principal_due > 0),
    interest_due numeric(18,2) NOT NULL CHECK (interest_due >= 0), cancelled_on date,
    PRIMARY KEY (loan_id, schedule_version, installment_no)
);
CREATE TABLE credit.loan_operation (
    operation_id bigint PRIMARY KEY, loan_id bigint NOT NULL REFERENCES credit.loan,
    operation_date date NOT NULL,
    operation_type text NOT NULL CHECK (operation_type IN ('DISBURSEMENT','REPAYMENT','PREPAYMENT','WRITE_OFF')),
    principal_amount numeric(18,2) NOT NULL CHECK (principal_amount >= 0),
    interest_amount numeric(18,2) NOT NULL CHECK (interest_amount >= 0),
    UNIQUE (operation_id, loan_id), CHECK (principal_amount + interest_amount > 0)
);
CREATE TABLE credit.payment_allocation (
    allocation_id bigint PRIMARY KEY, operation_id bigint NOT NULL,
    loan_id bigint NOT NULL, schedule_version integer NOT NULL,
    installment_no integer NOT NULL, component text NOT NULL CHECK (component IN ('Principal','Interest')),
    allocated_amount numeric(18,2) NOT NULL CHECK (allocated_amount > 0),
    FOREIGN KEY (operation_id, loan_id) REFERENCES credit.loan_operation(operation_id, loan_id),
    FOREIGN KEY (loan_id, schedule_version, installment_no)
        REFERENCES credit.payment_schedule(loan_id, schedule_version, installment_no),
    UNIQUE(operation_id, schedule_version, installment_no, component)
);
CREATE TABLE credit.loan_snapshot (
    snapshot_date date NOT NULL, loan_id bigint NOT NULL REFERENCES credit.loan,
    principal_balance numeric(18,2) NOT NULL CHECK (principal_balance >= 0),
    overdue_principal numeric(18,2) NOT NULL CHECK (overdue_principal BETWEEN 0 AND principal_balance),
    overdue_interest numeric(18,2) NOT NULL CHECK (overdue_interest >= 0),
    dpd integer NOT NULL CHECK (dpd >= 0),
    dpd_bucket text NOT NULL CHECK (dpd_bucket IN ('0','1-30','31-60','61-90','91+')),
    loan_status text NOT NULL CHECK (loan_status IN ('Active','Closed','Written Off')),
    ever_31_plus boolean NOT NULL,
    PRIMARY KEY (snapshot_date, loan_id),
    CHECK (dpd_bucket = CASE WHEN dpd=0 THEN '0' WHEN dpd<=30 THEN '1-30'
        WHEN dpd<=60 THEN '31-60' WHEN dpd<=90 THEN '61-90' ELSE '91+' END),
    CHECK (loan_status = 'Active' OR (principal_balance=0 AND dpd=0 AND overdue_principal=0 AND overdue_interest=0))
);
CREATE TABLE credit.loan_month_age (
    loan_id bigint NOT NULL REFERENCES credit.loan, months_on_book integer NOT NULL CHECK (months_on_book > 0),
    observation_date date NOT NULL, ever_31_plus boolean NOT NULL,
    PRIMARY KEY (loan_id, months_on_book)
);
CREATE TABLE credit.sales_plan (
    plan_month date NOT NULL, product_id integer NOT NULL REFERENCES credit.product,
    branch_id integer NOT NULL REFERENCES credit.branch,
    planned_amount numeric(18,2) NOT NULL CHECK (planned_amount > 0),
    planned_count integer NOT NULL CHECK (planned_count > 0),
    PRIMARY KEY (plan_month, product_id, branch_id), CHECK (extract(day FROM plan_month) = 1)
);
