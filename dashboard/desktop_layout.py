"""Presentation-only polish for the established 1920×1080 desktop report."""
import xml.etree.ElementTree as ET


def polish(store,entries,uid):
    # Keep the desktop grid; reserve a bottom strip for the native trial notice.
    store.update(width=1920,height=1080,keepRatio=True,adaptiveMode='AUTO')
    for story in store['stories']:
        for widget in story['widgets']:
            kind=widget['type'];props=widget['props'];name=widget['name']
            state=widget['states'];y=state['matrix'][5]
            if kind=='d-query-button':
                props.update(fontFamily='Arial',fontStyle={'fontSize':16,'fontWeight':'bold'})
            elif kind=='d-text-title':
                style=props['style']
                style.update(whiteSpace='pre-wrap',maxWidth=state['width'])
                if name.startswith('Navigate to '):style['fontSize']=16
                if 247<=y<374:
                    if name.endswith(' note'):
                        style['fontSize']=12
                        state['matrix'][5]=337;state['height']=30
                    elif name.endswith(' value'):
                        style['fontSize']=26 if story['name']=='Loan Details' else 30
                    elif props.get('value') and not name.endswith((' panel',' accent')):
                        style['fontSize']=13
                if name.startswith(('Transition column ','Transition opening ','Transition cell ')):
                    style['fontSize']=14
                if name.startswith('Registry ') and props.get('value','').startswith('=IF('):
                    style['fontSize']=14
                if name.startswith(('Operations ','Payment schedule ')) and props.get('value','').startswith('=IF('):
                    style['fontSize']=13
                if name.startswith('Vintage guide '):style['fontSize']=max(style['fontSize'],14)
                if name=='MOB range · Apply to update label':
                    props.update(value='MOB RANGE · APPLY',values='MOB RANGE · APPLY')
            elif kind.startswith('d-chart'):
                resource=store['resources'][props['configFile']]['name'].lstrip('/')
                xml=ET.fromstring(entries[resource])
                for font in xml.iter('FRFont'):font.set('size','112')
                entries[resource]=ET.tostring(xml,encoding='utf-8',xml_declaration=True)
        # The vendor notice is fixed to the browser bottom. At 1366x768 it
        # obscured the final registry/schedule rows. Tighten vertical spacing
        # without changing the desktop grid, text sizes or interaction bindings.
        for widget in story['widgets']:
            state=widget['states']
            state['matrix'][5]=round(state['matrix'][5]*0.9,3)
            background=(widget['type']=='d-text-title' and widget['props']['value']==''
                        and widget.get('border',{}).get('type')=='color')
            if background or widget['type'].startswith('d-chart'):
                state['height']=round(state['height']*0.9,3)
        # Keep opaque panels and stripes behind every label and value.
        background_ids={w['id'] for w in story['widgets'] if w['type']=='d-text-title'
                        and w['props']['value']=='' and w.get('border',{}).get('type')=='color'}
        story['widgets'].sort(key=lambda w:0 if w['id'] in background_ids else 1)
