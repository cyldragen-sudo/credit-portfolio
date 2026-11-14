"""Native quality page: KPI cards, exposure buckets, transition matrix and registry."""


def render(text,panel,combo,chart,value,navigate,link,open_loan,colors):
    navy,muted,teal,amber=colors

    def field(name,column,x,y,width,height=26,size=16,color=navy,bold=False):
        return text(name,'',x,y,width,height,size,color,bold,formula='='+value('quality_kpis',column))

    text('Quality identity','CREDIT ANALYTICS',36,24,700,22,12,teal,True)
    text('Quality title','Delinquency and Portfolio Quality',36,56,1500,49,35,navy,True)
    text('Quality subtitle','Retail lending · Past-due balances, migrations and contract review',36,111,1400,25,17,muted)
    text('Quality synthetic badge','SYNTHETIC DATA  /  RUB',1586,38,298,34,13,navy,True,background='#E3ECF6',align='center')
    field('Quality date','date_label',1586,88,298,28,18,navy,True)
    navigate('Delinquency and Portfolio Quality')
    combo('As of','p_date_key','filter_date',36,157,260)
    combo('Product','p_product_id','filter_product',316,157,320)
    combo('Region','p_region_id','filter_region',656,157,380)
    combo('Channel','p_channel_id','filter_channel',1056,157,310)
    button=text('Apply quality filters','',1386,180,138,42,background=teal)
    button.update(type='d-query-button',widgetType='button')
    button['props']={'value':'Apply','fontSize':16,'color':'#FFFFFF','background':teal}
    text('Quality period helper','Month-end reporting',1550,187,334,28,14,muted,align='right')

    cards=[('OVERDUE PRINCIPAL','overdue_principal_label','Unpaid scheduled principal',navy),
           ('OVERDUE INTEREST','overdue_interest_label','Unpaid scheduled interest',navy),
           ('31+ DPD EXPOSURE','ratio31_label','exposure31_note',amber),
           ('91+ DPD EXPOSURE','ratio91_label','exposure91_note',amber),
           ('PAST-DUE LOANS','past_due_loans_label','active_loans_note',navy),
           ('MONTHLY WRITE-OFFS','writeoff_label','writeoff_note',teal)]
    for index,(label,column,note,color) in enumerate(cards):
        x=36+index*310
        panel('Quality '+label+' panel',x,247,294,126)
        text('Quality '+label+' accent','',x,247,294,3,background=color)
        text('Quality '+label,label,x+18,263,258,22,12,muted,True)
        field('Quality '+label+' value',column,x+18,293,258,36,29,color,True)
        if note in ('exposure31_note','exposure91_note','active_loans_note','writeoff_note'):
            field('Quality '+label+' note',note,x+18,339,258,21,11,muted)
        else:text('Quality '+label+' note',note,x+18,339,258,21,11,muted)

    chart('quality_buckets',36,395,600,295,'Exposure by DPD bucket',
          'Full outstanding principal · RUB bn · active contracts',line=False)
    panel('Transition matrix panel',656,395,1228,295)
    text('Transition matrix title','Monthly transitions',678,410,1184,28,19,navy,True)
    field('Transition matrix dates','transition_note',678,445,1184,21,12,muted)
    states=['0','1-30','31-60','61-90','91+','Closed','Written Off']
    text('Transition row header','FROM / TO',678,474,174,22,11,muted,True)
    for column,label in enumerate(states):
        text('Transition column '+label,label,860+column*140,474,134,22,12,muted,True,align='center')
    for row in range(7):
        y=499+row*24
        text('Transition opening '+str(row),'',678,y,174,23,12,navy,True,
             formula='='+value('quality_transitions','row_label',row*7+1))
        for column in range(7):
            text('Transition cell {} {}'.format(row,column),'',860+column*140,y,134,23,12,navy,row==column,
                 background='#E3F0EC' if row==column else '#F7F9FC',
                 formula='='+value('quality_transitions','cell_label',row*7+column+1),align='center')
    text('Transition legend','Diagonal = unchanged state · 0% = no transitions · — = no opening contracts',678,674,1184,15,10,muted)

    panel('Loan registry panel',36,712,1848,300)
    text('Loan registry title','Loan registry · select a loan to open details',58,727,1050,29,19,navy,True)
    field('Registry page status','registry_page_label',58,762,550,23,13,navy,True)
    field('Registry status note','registry_note',540,762,620,23,11,muted)
    combo('Registry threshold · Apply to update','p_min_dpd','filter_min_dpd',1180,717,260)
    for label,column,x in [('← Previous','registry_prev_page',1460),('Next →','registry_next_page',1676)]:
        widget=text('Registry '+label,label,x,740,194,42,14,navy,True,background='#E3ECF6',align='center',
                    formula='="'+label+' "+'+value('quality_kpis',column))
        link(widget,'p_quality_page','='+value('quality_kpis',column))
    columns=[('LOAN','loan_reference',180),('CUSTOMER','customer_label',180),('PRODUCT','product_name',190),
             ('REGION','region_name',220),('CHANNEL','channel_name',160),('BALANCE, RUB','balance_label',220),
             ('OVERDUE P., RUB','overdue_principal_label',220),('OVERDUE I., RUB','overdue_interest_label',220),
             ('DPD','dpd_label',150)]
    for row in range(9):
        x=58;y=795 if row==0 else 817+(row-1)*23
        if row>0 and row%2==1:text('Registry row '+str(row),'',48,y,1824,22,background='#F7F9FC')
        for label,column,width in columns:
            align='right' if column in ('balance_label','overdue_principal_label','overdue_interest_label','dpd_label') else 'left'
            if row==0:text('Registry '+label+' header',label,x+5,y,width-14,21,10,muted,True,align=align)
            else:
                widget=text('Registry '+column+str(row),'',x+5,y,width-14,22,13,teal if column=='loan_reference' else navy,column=='loan_reference',
                    formula='=IF('+str(row)+'<=ROWCOUNT("quality_registry"),'+value('quality_registry',column,row)+',"")',align=align)
                if column=='loan_reference':open_loan(widget,row)
            x+=width
    field('Quality scope note','scope_note',36,1034,1480,24,11,muted)
    text('Quality synthetic footer','DEMO · NOT REGULATORY REPORTING',1530,1034,354,24,11,muted,align='right')
