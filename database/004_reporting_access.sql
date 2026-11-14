-- Optional: run as the database owner after creating your own LOGIN role.
-- Replace credit_report_user with the actual role name; no password is stored here.
GRANT USAGE ON SCHEMA credit TO credit_report_user;
GRANT SELECT ON ALL TABLES IN SCHEMA credit TO credit_report_user;
ALTER ROLE credit_report_user SET default_transaction_read_only = on;
-- SELECT is sufficient for all shipped datasets; no INSERT/UPDATE/DELETE is granted.
