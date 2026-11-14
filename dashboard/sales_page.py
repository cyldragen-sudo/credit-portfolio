"""Sales and Funnel layout using the shared native FineVIS widget helpers."""


def render(text,panel,combo,chart,value,navigate,colors):
    navy,muted,teal,amber=colors

    def field(name,column,x,y,width,height=26,size=16,color=navy,bold=False):
        return text(name,'',x,y,width,height,size,color,bold,formula='='+value('sales_kpis',column))

    text('Sales application identity','CREDIT ANALYTICS',36,24,700,22,12,teal,True)
    text('Sales title','Sales and Funnel',36,56,1200,49,37,navy,True)
    text('Sales subtitle','Retail lending · Origination, conversion and sales performance',36,111,1400,25,17,muted)
    text('Sales synthetic badge','SYNTHETIC DATA  /  RUB',1586,38,298,34,13,navy,True,background='#E3ECF6',align='center')
    field('Sales date','date_label',1586,88,298,28,18,navy,True)
    navigate('Sales and Funnel')
    combo('As of','p_date_key','filter_date',36,157,260)
    combo('Product','p_product_id','filter_product',316,157,320)
    combo('Region','p_region_id','filter_region',656,157,380)
    combo('Channel','p_channel_id','filter_channel',1056,157,310)
    button=text('Apply sales filters','',1386,180,138,42,background=teal)
    button.update(type='d-query-button',widgetType='button')
    button['props']={'value':'Apply','fontSize':16,'color':'#FFFFFF','background':teal}
    text('Sales period helper','Selected month',1550,187,334,28,14,muted,align='right')

    cards=[('DISBURSEMENTS','funded_amount_label','Funded during selected month',navy),
           ('FUNDED LOANS','funded_loans_label','Funded-date sales population',navy),
           ('AVG FUNDED AMOUNT','average_amount_label','Per funded loan',navy),
           ('APPLICATIONS','applications_label','Submitted during selected month',teal),
           ('APPROVAL RATE','approval_label','approval_note',teal),
           ('APPROVED TO FUNDED','conversion_label','conversion_note',amber)]
    for index,(label,column,note,color) in enumerate(cards):
        x=36+index*310
        panel('Sales '+label+' panel',x,247,294,126)
        text('Sales '+label+' accent','',x,247,294,3,background=color)
        text('Sales '+label,label,x+18,263,258,22,12,muted,True)
        field('Sales '+label+' value',column,x+18,293,258,36,29,color,True)
        if note in ('approval_note','conversion_note'):
            field('Sales '+label+' note',note,x+18,339,258,21,11,muted)
        else:
            text('Sales '+label+' note',note,x+18,339,258,21,11,muted)

    chart('sales_funnel_chart',36,395,570,295,'Application funnel',
          'Submitted in selected month · Outcomes at month end',line=False,footer=76,funnel=True)
    text('Funnel stage counts','',58,612,526,22,12,navy,True,
         formula='="Submitted: "+'+value('sales_kpis','submitted_applications')+'+"   ·   Approved: "+'+value('sales_kpis','approved_applications')+'+"   ·   Funded: "+'+value('sales_kpis','cohort_funded_applications'))
    field('Funnel other outcomes','funnel_summary',58,638,526,21,11,muted)
    field('Funnel elapsed time','funding_time_label',58,664,526,21,12,muted)
    chart('sales_trend_chart',626,395,690,295,'Disbursement trend',
          'Funded-date volumes · RUB m · completed month ends')
    chart('sales_channel_chart',1336,395,548,295,'Sales by channel',
          'Funded during selected month · RUB m',line=False)

    panel('Sales monthly plan panel',36,712,980,300)
    text('Monthly plan heading','Monthly plan vs actual',58,727,700,29,19,navy,True)
    text('Monthly plan scope badge','ALL CHANNELS',794,729,198,27,12,teal,True,background='#E2F0EC',align='center')
    text('Monthly plan units','Selected month, product and region · RUB m · channel filter does not apply',58,762,934,20,12,muted)
    plan_columns=[('PRODUCT','product_name',258),('LOANS','loans_label',120),('ACTUAL','actual_label',185),
                  ('PLAN','plan_label',185),('ATTAINMENT','attainment_label',180)]
    for row in range(4):
        x=58;y=799+row*39
        if row>0 and row%2==1:text('Plan row '+str(row),'',48,y,956,37,background='#F7F9FC')
        for label,column,width in plan_columns:
            if row==0:text('Plan '+label,label,x+5,y,width-12,25,11,muted,True)
            else:text('Plan '+column+str(row),'',x+5,y,width-12,30,16,navy,column=='product_name',
                formula='=IF('+str(row)+'<=ROWCOUNT("sales_plan_table"),'+value('sales_plan_table',column,row)+',"")')
            x+=width
    text('Plan explanation','Targets are synthetic monthly amounts; compare actuals within the same target scope.',58,975,934,20,11,muted)

    panel('Sales channel conversion panel',1036,712,848,300)
    text('Channel conversion heading','Channel conversion',1058,727,804,29,19,navy,True)
    text('Channel conversion units','Submission cohort · selected month · outcomes through report date',1058,762,804,20,12,muted)
    channel_columns=[('CHANNEL','channel_name',205),('SUBMITTED','applications_label',145),
                     ('APPROVAL','approval_label',145),('FUNDED / APPROVED','conversion_label',180),
                     ('AVG DAYS','days_label',125)]
    for row in range(5):
        x=1058;y=799+row*36
        if row>0 and row%2==1:text('Channel row '+str(row),'',1048,y,824,34,background='#F7F9FC')
        for label,column,width in channel_columns:
            if row==0:text('Channel '+label,label,x+5,y,width-12,25,10,muted,True)
            else:text('Channel '+column+str(row),'',x+5,y,width-12,29,15,navy,column=='channel_name',
                formula='=IF('+str(row)+'<=ROWCOUNT("sales_channel_table"),'+value('sales_channel_table',column,row)+',"")')
            x+=width
    field('Sales scope note','scope_note',36,1034,1480,24,11,muted)
    text('Sales synthetic footer','DEMO · NOT REGULATORY REPORTING',1530,1034,354,24,11,muted,align='right')
