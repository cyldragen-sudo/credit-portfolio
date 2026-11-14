"""Native vintage matrix, fixed-age cards and cumulative cohort curves."""


def render(text,panel,combo,chart,value,navigate,link,colors):
    navy,muted,teal,amber=colors

    def field(name,column,x,y,width,height=26,size=16,color=navy,bold=False):
        return text(name,'',x,y,width,height,size,color,bold,formula='='+value('vintage_kpis',column))

    text('Vintage identity','CREDIT ANALYTICS',36,24,600,22,12,teal,True)
    text('Vintage title','Vintage Analysis',36,56,1500,49,37,navy,True)
    text('Vintage subtitle','Retail lending · Compare origination cohorts at the same age',36,111,1400,25,17,muted)
    text('Vintage synthetic badge','SYNTHETIC DATA  /  RUB',1586,38,298,34,13,navy,True,background='#E3ECF6',align='center')
    field('Vintage date','date_label',1586,88,298,28,18,navy,True)
    navigate('Vintage Analysis')
    for name,param,dataset,x,width in [('As of','p_date_key','filter_date',36,260),
        ('Product','p_product_id','filter_product',316,320),('Region','p_region_id','filter_region',656,380),
        ('Channel','p_channel_id','filter_channel',1056,310)]:
        combo(name,param,dataset,x,157,width)
    button=text('Apply vintage filters','',1386,180,138,42,background=teal)
    button.update(type='d-query-button',widgetType='button')
    button['props']={'value':'Apply','fontSize':16,'color':'#FFFFFF','background':teal}
    text('Vintage period helper','Month-end reporting',1550,187,334,28,14,muted,align='right')

    cards=[('ORIGINAL LOANS','original_loans_label','All contracts in selected cohorts',navy),
        ('ORIGINAL FUNDED AMOUNT','original_amount_label','Original principal · RUB',navy),
        ('ORIGINATION COHORTS','cohort_count_label','cohort_window_label',teal),
        ('EVER 31+ · MOB 3','mob3_label','mob3_note',amber),
        ('EVER 31+ · MOB 6','mob6_label','mob6_note',amber),
        ('EVER 31+ · MOB 12','mob12_label','mob12_note',amber)]
    for index,(label,column,note,color) in enumerate(cards):
        x=36+index*310
        panel('Vintage '+label+' panel',x,247,294,126)
        text('Vintage '+label+' accent','',x,247,294,3,background=color)
        text('Vintage '+label,label,x+18,263,258,22,12,muted,True)
        field('Vintage '+label+' value',column,x+18,293,258,36,29,color,True)
        if note.endswith('_note') or note=='cohort_window_label':
            field('Vintage '+label+' note',note,x+18,339,258,21,11,muted)
        else:text('Vintage '+label+' note',note,x+18,339,258,21,11,muted)

    panel('Vintage matrix panel',36,395,1228,617)
    text('Vintage matrix title','Ever 31+ by origination cohort',58,410,790,30,22,navy,True)
    text('Vintage matrix definition','Cumulative % of original loans · complete monthly anniversaries',58,451,790,23,14,muted)
    combo('MOB range · Apply to update','p_vintage_mob_start','filter_vintage_mob',900,404,342,font_size=32)
    text('Vintage cohort header','COHORT',58,482,130,36,24,muted,True)
    text('Vintage loans header','LOANS',174,482,86,36,22,muted,True,align='right')
    for offset in range(6):
        text('Vintage MOB '+str(offset),'',282+offset*156,482,148,36,32,muted,True,align='center',
            formula='="M"+('+value('vintage_kpis','matrix_mob_start')+'+'+str(offset)+')')
    for cohort in range(6):
        y=528+cohort*60
        if cohort%2==0:text('Vintage stripe '+str(cohort),'',48,y,1204,56,background='#F7F9FC')
        start=cohort*6+1
        for name,column,x,width,align in [('cohort','cohort_label',58,130,'left'),('count','count_label',190,70,'right')]:
            text('Vintage '+name+' '+str(cohort),'',x,y,width,54,30,navy,True,align=align,
                formula='=IF('+str(start)+'<=ROWCOUNT("vintage_matrix_view"),'+value('vintage_matrix_view',column,start)+',"")')
        for offset in range(6):
            row=start+offset
            text('Vintage cell {} {}'.format(cohort,offset),'',282+offset*156,y,148,54,38,navy,False,align='center',
                formula='=IF('+str(row)+'<=ROWCOUNT("vintage_matrix_view"),'+value('vintage_matrix_view','cell_label',row)+',"")')
    for label,column,x in [('← Previous','matrix_prev_page',58),('Next →','matrix_next_page',980)]:
        widget=text('Vintage '+label,'',x,916,260,54,30,navy,True,background='#E3ECF6',align='center',
            formula='="'+label+' "+'+value('vintage_kpis',column))
        link(widget,'p_vintage_page','='+value('vintage_kpis',column))
    widget=field('Vintage matrix page status','matrix_page_label',340,928,628,34,28,navy,True)
    widget['props']['textAlign']='center'
    text('Vintage matrix legend','— = immature or unavailable · values rounded to 0.1% · newest first',58,984,1184,23,18,muted)

    chart('vintage_curves',1284,395,600,390,'Cohort curves',
          'Ever 31+ · % of original loans · observed anniversaries only',line=True,legend=True)
    panel('Vintage reading guide panel',1284,807,600,205)
    text('Vintage guide title','Read cohorts at equal age',1306,823,556,28,19,navy,True)
    text('Vintage guide metric','Each rate counts loans that ever reached 31+ DPD.',1306,864,556,22,13,navy)
    text('Vintage guide maturity','A cell waits until every loan reaches that anniversary.',1306,893,556,22,13,muted)
    text('Vintage guide cards','MOB cards pool mature cohorts using original loan counts.',1306,922,556,22,13,muted)
    text('Vintage guide curves','Curves sample every sixth available cohort, oldest first.',1306,951,556,22,13,muted)
    text('Vintage guide caveat','Cumulative ever delinquency is not a current loss rate.',1306,980,556,20,12,muted)
    field('Vintage scope note','scope_note',36,1034,1480,24,11,muted)
    text('Vintage synthetic footer','DEMO · NOT REGULATORY REPORTING',1530,1034,354,24,11,muted,align='right')
