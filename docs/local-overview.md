# Local Credit Portfolio Report

## Open the installed report

[Portfolio Overview](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=1)

[Sales and Funnel](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=2)

[Delinquency and Portfolio Quality](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=3)

[Vintage Analysis](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=4)

[Loan Details example](http://localhost:8075/webroot/decision/view/duchamp?viewlet=CREDIT_PORTFOLIO%252FPortfolio_Overview.fvs&page_number=5&p_loan_id=2170)

The installed path is `CREDIT_PORTFOLIO/Portfolio_Overview.fvs` inside FineReport's reportlets directory. It is a native FineVIS report: charts, text/formula widgets, dropdowns and the query button are native components. It does not embed a separate HTML application or browser database client. FineReport's vendor trial notice is preserved.

## Current desktop layout

All five pages use the compact 1920×1080 desktop canvas: six KPI cards in one row, charts beside each other and full tables. The readable Vintage matrix, wrapped notes and native Apply font are retained. See [desktop layout](desktop-layout.md).

## Database lifecycle

The persistent PostgreSQL 16 instance uses 127.0.0.1:55433 and database `credit_portfolio_demo`. It is independent of the existing 5432 database server. Its data, SCRAM credentials, connection material and backups are kept in the project `.private/` directory, restricted to the local user and excluded from releases. Do not delete `.private/` if you want to retain the deployed database.

Run from the project directory:

```bash
python3 src/local_database.py status
python3 src/local_database.py start
python3 src/local_database.py stop
```

After a computer restart, start the database and launch FineReport Designer normally before opening the link. This project does not install an automatic login/startup service. Initialization is `python3 src/local_database.py init`; it creates only a marked project database and reporting role, refuses occupied foreign targets, and reuses a matching deployed fixture without resetting its data. PostgreSQL binaries default to `/Library/PostgreSQL/16/bin`; set PG_BIN for another installation.

## Connection scopes

The portable report at `dashboard/report/Portfolio_Overview.fvs` references **CREDIT_PORTFOLIO** and contains no JDBC username or password. On another installation, configure this named connection using that installation's own SELECT-only account.

The local platform administration screen was not signed in, so deployment used the same supported native report-specific JDBC serialization pattern as the previous projects. The installed local report has an encrypted connection to `credit_report_user`; that account can SELECT and cannot UPDATE project data. Local report, dataset XML and credentials are private. The named connection is not newly registered in the platform-wide connection list. Switching to a centrally managed named connection later requires registering CREDIT_PORTFOLIO and installing the portable template.

## Filters and metrics

| Filter | Parameter | Values |
|---|---|---|
| As of | p_date_key | Numeric YYYYMMDD month end; 20241130 through 20261031 |
| Product | p_product_id | 0 All; 1 Personal Loan; 2 Auto Loan; 3 Mortgage |
| Region | p_region_id | 0 All; the six origination regions |
| Channel | p_channel_id | 0 All; 1 Branch; 2 Online; 3 Mobile App; 4 Partner |

Select values and press **Apply**. Use **Overview**, **Sales and Funnel**, **Portfolio Quality**, **Vintage Analysis** and **Loan Details** in the top navigation to change pages. Navigation explicitly carries all four applied parameters plus registry-only `p_min_dpd` (default 1) and `p_quality_page` (default 1), plus contract-specific `p_loan_id` (default 0), `p_operation_page` and `p_schedule_page` (both default 1), and Vintage view `p_vintage_page` / `p_vintage_mob_start` (both default1), and refreshes the target story. FineVIS updates page_number in the URL. URLs can restore numeric filters, for example appending `&p_product_id=2&p_region_id=1&p_date_key=20250831`. Bookmark an explicit parameter URL to restore a precise slice after a full reload; transient control selections are not automatically added to the URL.

Portfolio Quality's registry threshold changes only its contract list. Previous/Next targets are bounded, and a requested page beyond the available range is clamped. See [quality definitions](delinquency-quality.md).

On Sales and Funnel, the selected month determines funded-date sales and the application submission cohort. Its **ALL CHANNELS** product plan table intentionally ignores the channel filter while respecting month/product/region. All other sales components follow the four shared filters.

Every macro passes through FineReport INT before SQL substitution. Month-end dates are resolved from the database calendar and constrained to the fixture reporting window. Unknown numeric scopes produce zero balances, dash ratios, empty charts/table and a clear no-data message.

The overview reports portfolio balance, month-to-date funding, distinct active borrowers, month-over-month growth and full-loan DPD 31+/91+ exposure. Trends show completed month ends beginning November 2024. Regional borrowers are distinct within each region and must not be summed to recover the global borrower count. Regional balances are in RUB billions; card labels switch between millions and billions. See [metric definitions](metrics.md).

Vintage Analysis uses original contract counts and fully mature filtered cohorts. Its fixed-age cards pool eligible denominators; the matrix shows six cohorts and six MOB ages at a time, with full coverage via cohort paging and the MOB range selector. See [readability update](vintage-readable.md). See [vintage definitions](vintage-analysis.md).

## Rebuild using the installed vendor libraries

The generator/loader needs only Python. Native template rebuilding additionally needs a JDK and the user's installed licensed FineReport/FineVIS libraries; they are not distributed in the package. The validated local Java compiler is JDK 19.

```bash
python3 src/overview.py
mkdir -p build/java
javac -proc:none -cp '/Applications/FineReport/webapps/webroot/WEB-INF/lib/*' -d build/java dashboard/PortfolioDatasets.java
java -cp 'build/java:/Applications/FineReport/lib/*:/Applications/FineReport/webapps/webroot/WEB-INF/lib/*' PortfolioDatasets "$PWD" local
java -cp 'build/java:/Applications/FineReport/lib/*:/Applications/FineReport/webapps/webroot/WEB-INF/lib/*' PortfolioDatasets "$PWD"
python3 dashboard/build_report.py
python3 dashboard/build_report.py --local
python3 dashboard/install_report.py --replace
```

Set FINEREPORT_HOME when building against another install location. Adjust the Java classpath accordingly. Existing owned report targets are backed up privately before replacement. No ATM/DC reports, server settings, license files or vendor binaries are altered.

## Completed pages

All five native pages are built. Click a teal registry loan reference to open its contract; **Back to registry** restores the saved filters and registry page. Empty registry rows do nothing. Detail tables have separate eight-row pagination, reset on a new row selection. Details follow loan ID/date, while the other scope controls remain return context. See [Loan Details](loan-details.md).
