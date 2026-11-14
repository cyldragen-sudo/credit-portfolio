"""Dated contract detail with independent bounded operations/schedule pages."""
import re
from overview import ROOT,AS_OF,DEFAULTS

LOCAL_DEFAULTS=dict(p_loan_id=0,p_operation_page=1,p_schedule_page=1)


def money(expression):
    return "'RUB '||to_char("+expression+",'FM999,999,999,990.00')"


def build_queries():
    def adapt(name):
        return (ROOT/'queries'/name).read_text().strip().rstrip(';').replace("'${p_as_of}'::date",AS_OF).replace(
            '${p_loan_id}','${INT(p_loan_id)}').replace("'${p_start}'::date",'(SELECT report_start FROM credit.dataset_run)')
    header=adapt('11_loan_header.sql')
    operations=adapt('12_loan_operations.sql')
    schedule=adapt('13_loan_schedule.sql')
    base="""WITH selected AS ({header}),
      operations AS (SELECT o.* FROM ({operations}) o WHERE EXISTS(SELECT 1 FROM selected)),
      schedule AS (SELECT s.*,s.principal_paid+s.interest_paid paid_amount,
        s.principal_written_off+s.interest_written_off written_off_amount
        FROM ({schedule}) s WHERE EXISTS(SELECT 1 FROM selected)),
      counts AS (SELECT (SELECT count(*) FROM operations) operation_count,
        (SELECT count(*) FROM schedule) schedule_count),
      page_counts AS (SELECT *,greatest(1,ceil(operation_count::numeric/8))::integer operation_page_count,
        greatest(1,ceil(schedule_count::numeric/8))::integer schedule_page_count FROM counts),
      paging AS (SELECT *,least(greatest(${{INT(p_operation_page)}},1),operation_page_count)::integer operation_page_no,
        least(greatest(${{INT(p_schedule_page)}},1),schedule_page_count)::integer schedule_page_no FROM page_counts)""".format(
            header=header,operations=operations,schedule=schedule)
    fields=["coalesce(h.loan_id,0) selected_loan_id","{asof} as_of_date".format(asof=AS_OF),
        "to_char({asof},'DD Mon YYYY') date_label".format(asof=AS_OF),
        "CASE WHEN h.loan_id IS NULL THEN 'No loan selected' ELSE h.loan_reference||' · '||h.customer_label||' · '||h.product_name END identity_label",
        "CASE WHEN h.loan_id IS NULL THEN CASE WHEN ${INT(p_loan_id)}=0 THEN 'Open a loan from Portfolio Quality to view its details.' ELSE 'This loan is not available as of the selected date.' END ELSE 'Contract follows loan ID and As of; portfolio filters are retained for return.' END scope_note",
        "CASE WHEN h.loan_id IS NULL THEN '—' ELSE h.dpd::text END dpd_label",
        "coalesce(h.loan_status,'—') status_label",
        "coalesce(to_char(h.issue_date,'DD Mon YYYY'),'—') issue_label",
        "coalesce(to_char(h.maturity_date,'DD Mon YYYY'),'—') maturity_label",
        "coalesce(to_char(h.actual_close_date,'DD Mon YYYY'),'—') close_label",
        "coalesce(to_char(h.annual_rate,'FM990.00')||'%','—') rate_label",
        "coalesce(h.term_months||' months','—') term_label",
        "coalesce(h.region_name||' · '||h.branch_name||' · '||h.channel_name||' · Origination risk: '||h.risk_at_origination,'Select a contract in the loan registry.') origination_label",
        "coalesce((SELECT sum(cash_received) FROM operations),0) cash_received"]
    for column,label in [('principal_balance','balance_label'),('overdue_principal','overdue_principal_label'),
                         ('overdue_interest','overdue_interest_label'),('original_principal','original_label')]:
        fields.append("CASE WHEN h.loan_id IS NULL THEN '—' ELSE "+money('h.'+column)+' END '+label)
    fields.append("CASE WHEN h.loan_id IS NULL THEN '—' ELSE "+money('coalesce((SELECT sum(cash_received) FROM operations),0)')+' END cash_label')
    for prefix in ['operation','schedule']:
        fields.extend(["greatest(1,{p}_page_no-1) {p}_prev_page".format(p=prefix),
            "least({p}_page_count,{p}_page_no+1) {p}_next_page".format(p=prefix),
            "'Page '||{p}_page_no||' of '||{p}_page_count||' · '||{p}_count||' rows' {p}_page_label".format(p=prefix)])
    kpis=base+' SELECT h.*,p.*,'+','.join(fields)+' FROM paging p LEFT JOIN selected h ON true'
    operations_query=base+""", ordered AS (SELECT *,row_number() OVER(ORDER BY operation_date DESC,operation_id DESC) row_no FROM operations)
      SELECT o.*,to_char(operation_date,'DD Mon YY') date_label,
        initcap(replace(operation_type,'_',' ')) type_label,
        to_char(principal_amount,'FM999,999,990.00') principal_label,
        to_char(interest_amount,'FM999,999,990.00') interest_label,
        to_char(cash_received,'FM999,999,990.00') cash_label
      FROM ordered o CROSS JOIN paging p
      WHERE row_no BETWEEN (p.operation_page_no-1)*8+1 AND p.operation_page_no*8 ORDER BY row_no"""
    schedule_query=base+""", ordered AS (SELECT *,row_number() OVER(ORDER BY installment_no) row_no FROM schedule)
      SELECT s.*,installment_no::text installment_label,to_char(due_date,'DD Mon YY') date_label,
        to_char(principal_due,'FM999,999,990.00') principal_label,
        to_char(interest_due,'FM999,999,990.00') interest_label,
        to_char(paid_amount,'FM999,999,990.00') paid_label,
        to_char(written_off_amount,'FM999,999,990.00') writeoff_label,
        CASE WHEN cancelled_on IS NOT NULL THEN 'Cancelled'
          WHEN principal_paid+principal_written_off>=principal_due AND interest_paid+interest_written_off>=interest_due THEN 'Settled'
          WHEN due_date<{asof} THEN 'Overdue' WHEN due_date={asof} THEN 'Due today' ELSE 'Scheduled' END status_label
      FROM ordered s CROSS JOIN paging p
      WHERE row_no BETWEEN (p.schedule_page_no-1)*8+1 AND p.schedule_page_no*8 ORDER BY row_no""".format(asof=AS_OF)
    history="""WITH selected AS ({header}) SELECT s.snapshot_date,to_char(s.snapshot_date,'Mon YY') label,
      {series}::text series,{value} value FROM credit.loan_snapshot s JOIN credit.calendar c ON c.calendar_date=s.snapshot_date
      CROSS JOIN credit.dataset_run d WHERE s.loan_id=${{INT(p_loan_id)}} AND EXISTS(SELECT 1 FROM selected)
      AND s.snapshot_date BETWEEN d.report_start AND {asof} AND s.snapshot_date=c.month_end ORDER BY s.snapshot_date"""
    queries=dict(loan_kpis=kpis,loan_operations=operations_query,loan_schedule=schedule_query,
        loan_balance_chart=history.format(header=header,series="'Principal balance'",value='s.principal_balance/1000000',asof=AS_OF),
        loan_dpd_chart=history.format(header=header,series="'DPD'",value='s.dpd',asof=AS_OF))
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    return {name:dict(query=query,parameters={p:defaults[p] for p in defaults if '${INT('+p+')}' in query}) for name,query in queries.items()}


def expand(sql,**overrides):
    defaults=dict(DEFAULTS,**LOCAL_DEFAULTS)
    params=dict(defaults,**overrides)
    if set(params)!=set(defaults) or any(type(v) is not int or v<0 for v in params.values()):
        raise ValueError('Only known nonnegative integer parameters are allowed')
    return re.sub(r'\$\{INT\(([a-z_]+)\)\}',lambda m:str(params[m.group(1)]),sql)
