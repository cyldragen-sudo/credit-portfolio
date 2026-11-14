#!/usr/bin/env python3
"""Build the native FineVIS Portfolio Overview; keep local credentials private."""
import argparse
import copy
import html
import json
import os
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from sales_page import render as render_sales
from quality_page import render as render_quality
from vintage_page import render as render_vintage
from loan_page import render as render_loan
from desktop_layout import polish

ROOT=Path(__file__).resolve().parents[1]
FR=Path(os.environ.get('FINEREPORT_HOME','/Applications/FineReport'))
SAMPLE=FR/'webapps/webroot/WEB-INF/reportlets/The First FVS Dashboard.fvs'
BG='#F2F5FA'; WHITE='#FFFFFF'; NAVY='#152E4A'; MUTED='#687C91'; TEAL='#078B80'; AMBER='#CF8E27'; BORDER='#DFE7EF'
PARAMETERS=dict(p_date_key=20261031,p_product_id=0,p_region_id=0,p_channel_id=0,p_min_dpd=1,p_quality_page=1,
                p_loan_id=0,p_operation_page=1,p_schedule_page=1,p_vintage_page=1,p_vintage_mob_start=1)


def argb(color):
    return str(int('FF'+color.lstrip('#'),16)-2**32)


def build(target,local=False):
    target=Path(target)
    with zipfile.ZipFile(SAMPLE) as archive:
        root=ET.fromstring(archive.read('editor.tpl'))
        store=json.loads(root.find('DuchampTemplateAttr').get('store'))
        base=copy.deepcopy(store['stories'][0])
        prototype=copy.deepcopy(next(w for w in base['widgets'] if w['type']=='d-text-title'))
        chart_prototype=copy.deepcopy(next(w for w in base['widgets'] if w['type']=='d-chart-COLUMN'))
        chart_path=store['resources'][chart_prototype['props']['configFile']]['name'].lstrip('/')
        chart_xml=archive.read(chart_path)
    serial=0
    def uid():
        nonlocal serial
        serial+=1
        return str(uuid.uuid5(uuid.NAMESPACE_URL,'credit-portfolio-overview-'+str(serial)))
    store.update(id=uid(),name='Portfolio Overview',width=1920,height=1080,keepRatio=True,adaptiveMode='AUTO',
                 resources={},backgroundStories=[],stories=[],currentStory=0,computes={},
                 consanguinity={'templateComputes':[],'widgetComputesMap':{},'widgetTemplatesMap':{}},
                 parameterConfigs=[[],[],[],[],[]],controllerPanel={'enabled':False,'autoSearch':True,'widgets':[]},
                 cacheConfig={'enabled':False},previewConfig={'autoplay':False,'pageButtonDisplayPolicy':'never','arrows':False,'loop':False},
                 refreshConfig={'enabled':False,'interval':{'value':30,'type':'second'}})
    store['styleConfig']['theme_config'].update(background={'type':'color','value':BG},backgroundColor=BG,textColor=NAVY)
    page=copy.deepcopy(base)
    page.update(id=uid(),name='Portfolio Overview',widgets=[],border={'type':'color','value':BG},
                background={'type':'color','value':BG},isPreviewHidden=False)
    page['$modelId']=uid();page['alignmentLines']=[];page['transition']={'open':False,'duration':0}
    store['stories']=[page]
    metadata=json.loads((ROOT/'validation/native-datasets.json').read_text())
    columns={row['name']:row['columns'] for row in metadata}
    entries={}

    def register(widget,field,config):
        key=widget['id']+'.'+field
        store['computes'][key]=config
        store['consanguinity']['widgetComputesMap'].setdefault(widget['id'],[]).append(key)

    def value(dataset,column,row=1):
        return 'VALUE("{}",{},{})'.format(dataset,columns[dataset].index(column)+1,row)

    def text(name,content,x,y,width,height=26,size=16,color=NAVY,bold=False,background=None,formula=None,align='left'):
        widget=copy.deepcopy(prototype)
        widget.update(id=uid(),name=name,parent='',children=[],actions=[],events=[],widgetEvents=[],hide=False,lock=False)
        widget['states'].update(width=width,height=height,matrix=[1,0,0,1,x,y],animation={})
        widget['props'].update(value=content,values=content,fontFamily='Arial',
                               style={'fontSize':size,'fontWeight':'bold' if bold else 'normal'},
                               color=color,textAlign=align,fontLineHeight='normal',letterSpacing=0,wordSpacing=0)
        widget['border']={'type':'color','value':background} if background else {'type':'empty'}
        widget['borderLine']={'borderStyle':'none','borderWidth':1,'borderColor':BORDER}
        if formula:
            widget['props']['value']=formula
            widget['props']['values']={'id':uid(),'source':{'type':'formula','formula':formula},
                                       'formatter':{'type':'normal','value':''},'conditionStyles':[]}
            register(widget,'value',{'type':'formula','columns':[{'formula':formula}]})
        page['widgets'].append(widget)
        return widget

    def panel(name,x,y,w,h):
        return text(name,'',x,y,w,h,background=WHITE)

    def formula(name,column,x,y,w,h=26,size=16,color=NAVY,bold=False):
        return text(name,'',x,y,w,h,size,color,bold,formula='='+value('overview_kpis',column))

    def combo(name,parameter,dataset,x,y,width,font_size=16):
        text(name+' label',name.upper(),x,y,width,18,11,MUTED,True)
        widget=text(name+' selector','',x,y+23,width,42,background=WHITE)
        widget.update(type='d-controller-combo',version='0.0.1',widgetType='controller',displayName='Drop-down Box',
                      events=[{'type':'MOUNTED'},{'type':'EDIT_FINISH'}],refresh=False)
        widget['props']={'fontSize':font_size,'enable':True,
            'validation':{'allowEmpty':{'open':False,'errorTip':'Select a value'},'customValue':{'open':False,'errorTip':''}},
            'valueConfig':{'type':'formula','payload':{'formula':'=$'+parameter}},'styleType':'default',
            'styleConfig':{'fontFamily':'Arial','fontAttr':{'fontSize':font_size},'color':NAVY,'iconColor':MUTED,'highlightColor':TEAL},
            'relatedParams':{'valueConfig':parameter},'multiSelect':False,
            'dataDictionaryConfig':{'value':{'type':'dataQuery','datasetName':dataset,
              'itemValue':{'type':'name','value':'id'},'itemText':{'type':'name','value':'label'}},'repeatable':False}}
        register(widget,'valueConfig',{'type':'formula','columns':[{'formula':'=$'+parameter}]})
        register(widget,'dataDictionaryConfig',{'type':'dataset','datasetName':dataset,
            'columns':[{'name':'id'},{'name':'label'}],'payload':{'repeatable':False}})
        return widget

    def chart(dataset,x,y,w,h,title,subtitle,line=True,legend=False,footer=0,funnel=False):
        panel(title+' panel',x,y,w,h)
        text(title+' heading',title,x+22,y+15,w-44,28,19,NAVY,True)
        text(title+' units',subtitle,x+22,y+47,w-44,20,12,MUTED)
        widget=copy.deepcopy(chart_prototype)
        widget.update(id=uid(),name=title,parent='',children=[],actions=[],widgetEvents=[],events=[],
                      type='d-chart-FUNNEL' if funnel else 'd-chart-LINE' if line else 'd-chart-COLUMN')
        widget['states'].update(width=w-24,height=h-78-footer,matrix=[1,0,0,1,x+12,y+70],animation={})
        resource_id=uid();filename=widget['id']+'.chart';widget['props']={'configFile':resource_id}
        page['widgets'].append(widget)
        config=ET.fromstring(chart_xml)
        chart_node=config.find('./Chart/Chart')
        if line or funnel:
            old=chart_node.find('Plot');position=list(chart_node).index(old);chart_node.remove(old)
            chart_node.insert(position,ET.parse(ROOT/('build/default-funnel.xml' if funnel else 'build/default-line.xml')).getroot())
        definition=config.find('.//ChartDefinition/OneValueCDDefinition')
        definition.set('seriesName','series');definition.set('valueName','value')
        definition.find('TableData/Name').text=dataset;definition.find('CategoryName').set('value','label')
        if funnel:
            definition.set('seriesName','label')
            definition.find('CategoryName').set('value','None')
        for font in config.iter('FRFont'):
            font.set('name','Arial');font.set('size','96')
            color=font.find('foreground/FineColor')
            if color is not None:color.set('color',argb(MUTED))
        for node in config.findall('.//Legend4VanChart/Legend/Attr'):
            node.set('visible','true' if legend else 'false')
        for node in config.findall('.//Title4VanChart/Title/TitleVisible'):
            node.set('value','false')
        fill=config.find('.//Plot/newPlotFillStyle/AttrFillStyle')
        if fill is not None:
            if fill.find('ColorList') is None:ET.SubElement(fill,'ColorList')
            fill.find('AFStyle').set('colorStyle','1')
            fill.find('PredefinedStyle').set('themed','false')
        for node in config.findall('.//ColorList'):
            for child in list(node):node.remove(child)
            for color in [TEAL,AMBER,'#5279A2','#8B79B2']:
                entry=ET.SubElement(node,'OColor');colvalue=ET.SubElement(entry,'colvalue')
                ET.SubElement(colvalue,'FineColor',color=argb(color),hor='-1',ver='-1')
        for node in config.findall('.//isCustomFillStyle'):node.set('isCustomFillStyle','true')
        for node in config.findall('.//newLineColor/mainGridColor/FineColor'):node.set('color',argb('#E8EDF3'))
        for node in config.findall('.//newLineColor/lineColor/FineColor'):node.set('color',argb(BORDER))
        for node in config.findall('.//AttrTooltip/GI/AttrBackground/Background'):
            node.set('name','ColorBackground')
            color=node.find('color/FineColor')
            if color is not None:color.set('color',argb(WHITE))
        for node in config.findall('.//AttrTooltip/GI/AttrAlpha/Attr'):node.set('alpha','0.96')
        for node in config.findall('.//Format'):
            if node.get('class')=='com.fr.base.CoreDecimalFormat':node.text='#,##0.00'
        entries[filename]=ET.tostring(config,encoding='utf-8',xml_declaration=True)
        store['resources'][resource_id]={'id':resource_id,'type':'chart','name':'/'+filename,'payload':{'isPrivate':True}}
        register(widget,'config',{'type':'chart','id':widget['id']})

    def transition(widget,target,overrides=None,guard=False):
        overrides=overrides or {}
        parameters=[{'name':'nav_'+name,'type':'formula','value':overrides.get(name,'=$'+name)} for name in PARAMETERS]
        target_expression='{'+','.join(name+':Number(nav_'+name+')' for name in PARAMETERS)+'}'
        code='duchamp.switchStory('+json.dumps(target)+','+target_expression+');'
        if guard:code='if(Number(nav_p_loan_id)>0){'+code+'}'
        action={'id':uid(),'name':'Open '+target,'type':'javascript','enabled':True,'condition':None,
                'body':{'code':code,'parameters':parameters}}
        widget['widgetEvents']=[{'target':'','events':[{'id':uid(),'name':'Navigate','trigger':'CLICK',
            'enabled':True,'mode':'selective','actions':[action]}]}]
        key=widget['id']+'-'+action['id']+'.parameters'
        store['computes'][key]={'type':'formula','columns':[{'formula':p['value']} for p in parameters]}
        store['consanguinity']['widgetComputesMap'].setdefault(widget['id'],[]).append(key)

    def open_loan(widget,row):
        transition(widget,'Loan Details',dict(p_loan_id='=IF('+str(row)+'<=ROWCOUNT("quality_registry"),'+value('quality_registry','loan_id',row)+',0)',
            p_operation_page='=1',p_schedule_page='=1'),guard=True)

    def navigation(active):
        x=660
        for label,target,width in [('Overview','Portfolio Overview',130),('Sales and Funnel','Sales and Funnel',190),
                                   ('Portfolio Quality','Delinquency and Portfolio Quality',200),('Vintage Analysis','Vintage Analysis',170),
                                   ('Loan Details','Loan Details',150)]:
            widget=text('Navigate to '+target,label,x,22,width,32,14,
                        TEAL if active==target else NAVY,True,
                        background='#DDEFEA' if active==target else WHITE,align='center')
            x+=width+12
            if active==target:continue
            transition(widget,target)

    def link(widget,parameter,expression):
        action={'id':uid(),'name':'Update table page','type':'widgetLink','enabled':True,'condition':None,
            'body':{'isAll':True,'widgets':[],'parameters':[{'name':parameter,'type':'formula','value':expression}]}}
        widget['widgetEvents']=[{'target':'','events':[{'id':uid(),'name':'Page registry','trigger':'CLICK',
            'enabled':True,'mode':'selective','actions':[action]}]}]
        key=widget['id']+'-'+action['id']+'.parameters'
        store['computes'][key]={'type':'formula','columns':[{'formula':expression}]}
        store['consanguinity']['widgetComputesMap'].setdefault(widget['id'],[]).append(key)

    text('Application identity','CREDIT ANALYTICS',36,24,700,22,12,TEAL,True)
    text('Page title','Portfolio Overview',36,56,1200,49,37,NAVY,True)
    text('Page subtitle','Retail lending · Growth, composition and credit quality',36,111,1400,25,17,MUTED)
    text('Synthetic badge','SYNTHETIC DATA  /  RUB',1586,38,298,34,13,NAVY,True,background='#E3ECF6',align='center')
    formula('As-of label','date_label',1586,88,298,28,18,NAVY,True)
    combo('As of','p_date_key','filter_date',36,157,260)
    combo('Product','p_product_id','filter_product',316,157,320)
    combo('Region','p_region_id','filter_region',656,157,380)
    combo('Channel','p_channel_id','filter_channel',1056,157,310)
    button=text('Apply filters','',1386,180,138,42,background=TEAL)
    button.update(type='d-query-button',widgetType='button')
    button['props']={'value':'Apply','fontSize':16,'color':WHITE,'background':TEAL}
    text('Filter helper','Month-end reporting',1550,187,334,28,14,MUTED,align='right')

    cards=[('PORTFOLIO BALANCE','portfolio_label','comparison_note',NAVY),
           ('MTD DISBURSEMENTS','funding_label','funding_note',NAVY),
           ('ACTIVE BORROWERS','borrowers_label','active_loans_label',NAVY),
           ('MONTHLY GROWTH','growth_label','growth_amount_label',TEAL),
           ('31+ DPD EXPOSURE','ratio_31_label','exposure_31_label',AMBER),
           ('91+ DPD EXPOSURE','ratio_91_label','exposure_91_label',AMBER)]
    for index,(label,column,note,color) in enumerate(cards):
        x=36+index*310
        panel(label+' panel',x,247,294,126)
        text(label+' accent','',x,247,294,3,background=color)
        text(label,label,x+18,263,258,22,12,MUTED,True)
        formula(label+' value',column,x+18,293,258,36,29,color,True)
        formula(label+' note',note,x+18,339,258,21,12,MUTED)

    chart('balance_chart',36,395,910,295,'Portfolio trend','Outstanding principal · RUB bn · completed month ends')
    chart('quality_chart',966,395,918,295,'Delinquency trend','Whole-loan principal exposure · % of portfolio',legend=True)
    chart('product_chart',36,712,600,300,'Product composition','Outstanding principal · RUB bn',line=False)
    panel('Region performance panel',656,712,1228,300)
    text('Region performance heading','Regional performance',678,727,900,29,19,NAVY,True)
    text('Region performance units','Origination region · balances in RUB bn · growth vs previous month end',678,762,1184,20,12,MUTED)
    headings=[('REGION','region_name',278),('BALANCE','balance_label',160),('GROWTH','growth_label',160),
              ('BORROWERS','borrowers_label',160),('31+ DPD','ratio31_label',160),('91+ DPD','ratio91_label',160)]
    for row in range(0,7):
        x=678;y=795+row*27
        if row>0 and row%2==1:text('Region row '+str(row),'',670,y,1198,26,background='#F7F9FC')
        for heading,column,width in headings:
            if row==0:text(heading+' header',heading,x+5,y,width-12,23,11,MUTED,True)
            else:
                expression='=IF({row}<=ROWCOUNT("region_table"),{value},"")'.format(row=row,value=value('region_table',column,row))
                text(column+' '+str(row),'',x+5,y,width-12,25,15,NAVY,column=='region_name',formula=expression)
            x+=width
    formula('Scope note','scope_note',36,1034,1450,24,12,MUTED)
    text('Synthetic footer','DEMO · NOT REGULATORY REPORTING',1530,1034,354,24,11,MUTED,align='right')

    navigation('Portfolio Overview')
    page=copy.deepcopy(base)
    page.update(id=uid(),name='Sales and Funnel',widgets=[],border={'type':'color','value':BG},
                background={'type':'color','value':BG},isPreviewHidden=False)
    page['$modelId']=uid();page['alignmentLines']=[];page['transition']={'open':False,'duration':0}
    store['stories'].append(page)
    render_sales(text,panel,combo,chart,value,navigation,(NAVY,MUTED,TEAL,AMBER))

    page=copy.deepcopy(base)
    page.update(id=uid(),name='Delinquency and Portfolio Quality',widgets=[],border={'type':'color','value':BG},
                background={'type':'color','value':BG},isPreviewHidden=False)
    page['$modelId']=uid();page['alignmentLines']=[];page['transition']={'open':False,'duration':0}
    store['stories'].append(page)
    render_quality(text,panel,combo,chart,value,navigation,link,open_loan,(NAVY,MUTED,TEAL,AMBER))

    page=copy.deepcopy(base)
    page.update(id=uid(),name='Vintage Analysis',widgets=[],border={'type':'color','value':BG},
                background={'type':'color','value':BG},isPreviewHidden=False)
    page['$modelId']=uid();page['alignmentLines']=[];page['transition']={'open':False,'duration':0}
    store['stories'].append(page)
    render_vintage(text,panel,combo,chart,value,navigation,link,(NAVY,MUTED,TEAL,AMBER))

    page=copy.deepcopy(base)
    page.update(id=uid(),name='Loan Details',widgets=[],border={'type':'color','value':BG},
                background={'type':'color','value':BG},isPreviewHidden=False)
    page['$modelId']=uid();page['alignmentLines']=[];page['transition']={'open':False,'duration':0}
    store['stories'].append(page)
    render_loan(text,panel,combo,chart,value,navigation,transition,link,(NAVY,MUTED,TEAL,AMBER))

    polish(store,entries,uid)

    for node in list(root):
        if node.tag in ('TableDataMap','Parameters'):root.remove(node)
    params=ET.SubElement(root,'Parameters')
    for name,value_ in PARAMETERS.items():
        node=ET.SubElement(params,'Parameter');ET.SubElement(node,'Attributes',name=name);ET.SubElement(node,'O',t='I').text=str(value_)
    template=root.find('DuchampTemplateAttr')
    template.set('duchampLoaded','')
    template.set('store',json.dumps(store,ensure_ascii=False,separators=(',',':')))
    root.append(ET.parse(ROOT/('.private/datasets.xml' if local else 'dashboard/datasets.xml')).getroot())
    xml=ET.tostring(root,encoding='unicode')
    xml=re.sub(r'<Query>(.*?)</Query>',lambda match:'<Query><![CDATA['+html.unescape(match[1]).replace(']]>',']]]]><![CDATA[>')+']]></Query>',xml,flags=re.S)
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('editor.tpl',xml.encode('utf-8'))
        for filename,content in entries.items():archive.writestr(filename,content)
    if local:target.chmod(0o600)
    widget_count=sum(len(story['widgets']) for story in store['stories'])
    chart_count=sum(w['type'].startswith('d-chart') for story in store['stories'] for w in story['widgets'])
    print('Built '+('private local' if local else 'portable named-connection')+' report: '+str(len(store['stories']))+' pages, '+str(widget_count)+' native widgets, '+str(len(metadata))+' datasets, '+str(chart_count)+' native charts.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local',action='store_true')
    args=parser.parse_args()
    build(ROOT/('.private/Portfolio_Overview.fvs' if args.local else 'dashboard/report/Portfolio_Overview.fvs'),args.local)
