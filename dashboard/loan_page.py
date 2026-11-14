"""Native selected-contract page with dated history and full paged records."""


def render(text,panel,combo,chart,value,navigate,transition,link,colors):
    navy,muted,teal,amber=colors

    def field(name,column,x,y,width,height=26,size=16,color=navy,bold=False):
        return text(name,'',x,y,width,height,size,color,bold,formula='='+value('loan_kpis',column))

    text('Loan identity','CREDIT ANALYTICS',36,24,600,22,12,teal,True)
    text('Loan title','Loan Details',36,56,1500,49,37,navy,True)
    field('Loan selected contract','identity_label',36,111,1400,25,17,muted)
    text('Loan synthetic badge','SYNTHETIC DATA  /  RUB',1586,38,298,34,13,navy,True,background='#E3ECF6',align='center')
    field('Loan date','date_label',1586,88,298,28,18,navy,True)
    navigate('Loan Details')
    for name,param,dataset,x,width in [('As of','p_date_key','filter_date',36,260),
        ('Product','p_product_id','filter_product',316,320),('Region','p_region_id','filter_region',656,380),
        ('Channel','p_channel_id','filter_channel',1056,310)]:combo(name,param,dataset,x,157,width)
    button=text('Apply loan date','',1386,180,138,42,background=teal)
    button.update(type='d-query-button',widgetType='button')
    button['props']={'value':'Apply','fontSize':16,'color':'#FFFFFF','background':teal}
    back=text('Return to saved registry','← Back to registry',1550,180,334,42,15,navy,True,background='#E3ECF6',align='center')
    transition(back,'Delinquency and Portfolio Quality')

    cards=[('PRINCIPAL BALANCE','balance_label','Outstanding principal · RUB',navy),
        ('OVERDUE PRINCIPAL','overdue_principal_label','Unpaid scheduled principal · RUB',amber),
        ('OVERDUE INTEREST','overdue_interest_label','Unpaid scheduled interest · RUB',amber),
        ('DAYS PAST DUE','dpd_label','As of selected month end',amber),
        ('CONTRACT STATUS','status_label','Observed state on selected date',navy),
        ('CASH RECEIVED','cash_label','Cumulative receipts · excludes write-offs',teal)]
    for index,(label,column,note,color) in enumerate(cards):
        x=36+index*310
        panel('Loan '+label+' panel',x,247,294,126)
        text('Loan '+label+' accent','',x,247,294,3,background=color)
        text('Loan '+label,label,x+18,263,258,22,12,muted,True)
        field('Loan '+label+' value',column,x+18,293,258,36,24,color,True)
        text('Loan '+label+' note',note,x+18,339,258,21,10,muted)

    panel('Loan contract attributes panel',36,395,1848,100)
    for i,(label,column) in enumerate([('ORIGINAL PRINCIPAL','original_label'),('ANNUAL RATE','rate_label'),
        ('ORIGINAL TERM','term_label'),('ISSUED','issue_label'),('CONTRACTUAL MATURITY','maturity_label'),('OBSERVED CLOSE DATE','close_label')]):
        x=54+i*310
        text('Loan attribute '+label,label,x,408,258,18,11,muted,True)
        field('Loan attribute '+column,column,x,432,258,26,18,navy,True)
    field('Loan origination context','origination_label',54,470,1806,20,12,muted)

    chart('loan_balance_chart',36,517,902,215,'Principal history','Month-end outstanding principal · RUB m',line=True)
    chart('loan_dpd_chart',960,517,924,215,'Delinquency history','Month-end days past due · days',line=True)

    def table(dataset,prefix,title,x,width,columns):
        y=754
        panel(title+' panel',x,y,width,258)
        text(title+' heading',title,x+22,y+15,330,25,18,navy,True)
        field(title+' page status',prefix+'_page_label',x+22,y+48,width-44,20,12,muted)
        for label,target,button_x in [('← Previous',prefix+'_prev_page',x+width-386),('Next →',prefix+'_next_page',x+width-202)]:
            widget=text(title+' '+label,'',button_x,y+12,180,32,12,navy,True,background='#E3ECF6',align='center',
                formula='="'+label+' "+'+value('loan_kpis',target))
            link(widget,'p_'+prefix+'_page','='+value('loan_kpis',target))
        for row in range(9):
            row_y=y+73 if row==0 else y+97+(row-1)*19.5
            if row>0 and row%2==1:text(title+' stripe '+str(row),'',x+12,row_y,width-24,20,background='#F7F9FC')
            column_x=x+22
            for label,column,column_width,numeric in columns:
                align='right' if numeric else 'left'
                if row==0:text(title+' '+label,label,column_x,row_y,column_width-10,18,10,muted,True,align=align)
                else:text(title+' '+column+str(row),'',column_x,row_y,column_width-10,20,12,navy,False,align=align,
                    formula='=IF('+str(row)+'<=ROWCOUNT("'+dataset+'"),'+value(dataset,column,row)+',"")')
                column_x+=column_width

    table('loan_operations','operation','Operations',36,902,[('DATE','date_label',125,False),
        ('TYPE','type_label',175,False),('PRINCIPAL, RUB','principal_label',185,True),
        ('INTEREST, RUB','interest_label',175,True),('CASH, RUB','cash_label',180,True)])
    table('loan_schedule','schedule','Payment schedule',960,924,[('#','installment_label',35,False),
        ('DUE DATE','date_label',110,False),('PRINCIPAL, RUB','principal_label',150,True),
        ('INTEREST, RUB','interest_label',140,True),('PAID, RUB','paid_label',160,True),
        ('WRITTEN OFF, RUB','writeoff_label',145,True),('STATUS','status_label',125,False)])
    field('Loan scope note','scope_note',36,1034,1480,24,11,muted)
    text('Loan synthetic footer','DEMO · NOT REGULATORY REPORTING',1530,1034,354,24,11,muted,align='right')
