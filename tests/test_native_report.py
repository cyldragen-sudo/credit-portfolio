import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class NativeReportTests(unittest.TestCase):
    def test_portable_report_has_live_native_bindings_and_no_credentials(self):
        module_file=ROOT/'dashboard/build_report.py'
        self.assertTrue(module_file.exists(),'Native overview builder is not implemented')
        spec=importlib.util.spec_from_file_location('credit_report_builder',module_file)
        builder=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'Portfolio_Overview.fvs'
            builder.build(target,local=False)
            with zipfile.ZipFile(target) as archive:
                root=ET.fromstring(archive.read('editor.tpl'))
                store=json.loads(root.find('DuchampTemplateAttr').get('store'))
                self.assertEqual(len(store['stories']),5)
                self.assertEqual(store['stories'][0]['name'],'Portfolio Overview')
                self.assertEqual(store['stories'][1]['name'],'Sales and Funnel')
                self.assertEqual(store['stories'][2]['name'],'Delinquency and Portfolio Quality')
                self.assertEqual(store['stories'][3]['name'],'Vintage Analysis')
                self.assertEqual(store['stories'][4]['name'],'Loan Details')
                datasets=root.findall('TableDataMap/TableData')
                self.assertEqual(len(datasets),31)
                self.assertTrue(all(d.find('Connection').get('class').endswith('NameDatabaseConnection') for d in datasets))
                self.assertNotIn(b'JDBCDatabaseConnection',archive.read('editor.tpl'))
                self.assertGreaterEqual(len([w for w in store['stories'][0]['widgets'] if w['type'].startswith('d-chart')]),3)
                self.assertEqual(len([w for w in store['stories'][0]['widgets'] if w['type']=='d-controller-combo']),4)
                self.assertEqual(len([w for w in store['stories'][0]['widgets'] if w['type']=='d-query-button']),1)
                for index,story in enumerate(store['stories']):
                    self.assertEqual(len([w for w in story['widgets'] if w['type'].startswith('d-chart')]),[3,3,1,1,2][index])
                    self.assertEqual(len([w for w in story['widgets'] if w['type']=='d-controller-combo']),5 if index in (2,3) else 4)
                    self.assertEqual(len([w for w in story['widgets'] if w['type']=='d-query-button']),1)
                    for target_name in [s['name'] for s in store['stories'] if s is not story]:
                        actions=[a for w in story['widgets'] if w['name'].startswith('Navigate to ') for group in w.get('widgetEvents',[])
                                 for event in group.get('events',[]) for a in event.get('actions',[])
                                 if a.get('type')=='javascript' and target_name in a.get('body',{}).get('code','')]
                        self.assertEqual(len(actions),1)
                        self.assertEqual({p['value'] for p in actions[0]['body']['parameters']},
                                         {'=$p_date_key','=$p_product_id','=$p_region_id','=$p_channel_id','=$p_min_dpd','=$p_quality_page','=$p_loan_id','=$p_operation_page','=$p_schedule_page','=$p_vintage_page','=$p_vintage_mob_start'})
                drills=[a for w in store['stories'][2]['widgets'] if w['name'].startswith('Registry loan_reference')
                        for g in w.get('widgetEvents',[]) for e in g.get('events',[]) for a in e.get('actions',[])]
                self.assertEqual(len(drills),8)
                loan_column=next(d['columns'].index('loan_id')+1 for d in json.loads((ROOT/'validation/native-datasets.json').read_text()) if d['name']=='quality_registry')
                for row,action in enumerate(drills,1):
                    parameters={p['name']:p['value'] for p in action['body']['parameters']}
                    self.assertIn('Number(nav_p_loan_id)>0',action['body']['code'])
                    self.assertEqual(parameters['nav_p_loan_id'], '=IF('+str(row)+'<=ROWCOUNT("quality_registry"),VALUE("quality_registry",'+str(loan_column)+','+str(row)+'),0)')
                    self.assertEqual(parameters['nav_p_operation_page'],'=1')
                    self.assertEqual(parameters['nav_p_schedule_page'],'=1')
                    self.assertEqual(len(parameters),11)
                detail_paging=[a for w in store['stories'][4]['widgets'] for g in w.get('widgetEvents',[])
                               for e in g.get('events',[]) for a in e.get('actions',[]) if a['type']=='widgetLink']
                self.assertEqual(len(detail_paging),4)
                self.assertEqual({a['body']['parameters'][0]['name'] for a in detail_paging},{'p_operation_page','p_schedule_page'})
                paging=[a for w in store['stories'][2]['widgets'] for g in w.get('widgetEvents',[])
                        for e in g.get('events',[]) for a in e.get('actions',[]) if a.get('type')=='widgetLink']
                self.assertEqual(len(paging),2)
                self.assertTrue(all(a['body']['parameters'][0]['name']=='p_quality_page' for a in paging))
                funnel=next(w for w in store['stories'][1]['widgets'] if w['name']=='Application funnel')
                resource=store['resources'][funnel['props']['configFile']]['name'].lstrip('/')
                self.assertTrue(ET.fromstring(archive.read(resource)).find('.//Plot').get('class').endswith('VanChartFunnelPlot'))

    def test_desktop_composition_retains_readability_fixes(self):
        spec=importlib.util.spec_from_file_location('desktop_builder',ROOT/'dashboard/build_report.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'desktop.fvs';builder.build(target)
            with zipfile.ZipFile(target) as archive:
                store=json.loads(ET.fromstring(archive.read('editor.tpl')).find('DuchampTemplateAttr').get('store'))
        self.assertEqual((store['width'],store['height'],store['adaptiveMode']),(1920,1080,'AUTO'))
        for story in store['stories']:
            widgets=story['widgets']
            cards=[w for w in widgets if w['name'].endswith(' value') and 247<=w['states']['matrix'][5]<374]
            self.assertEqual(len(cards),6)
            self.assertEqual(len({w['states']['matrix'][5] for w in cards}),1)
            self.assertEqual(len({w['states']['matrix'][4] for w in cards}),6)
            button=next(w for w in widgets if w['type']=='d-query-button')
            self.assertEqual(button['props']['fontStyle']['fontSize'],16)
            for w in widgets:
                x,y=w['states']['matrix'][4:6]
                self.assertGreaterEqual(x,0)
                self.assertLessEqual(x+w['states']['width'],1920)
                self.assertLessEqual(y+w['states']['height'],1080)
                if w['name'].endswith(' note') and 247<=y<374:
                    self.assertEqual(w['props']['style']['whiteSpace'],'pre-wrap')
                    self.assertGreaterEqual(w['states']['height'],28)
            charts=[w for w in widgets if w['type'].startswith('d-chart')]
            if len(charts)>1:self.assertGreater(len({w['states']['matrix'][4] for w in charts}),1)
        for page,names in [(2,['Registry loan_reference1','Registry balance_label1','Registry dpd_label1']),
                           (4,['Payment schedule installment_label1','Payment schedule principal_label1','Payment schedule status_label1'])]:
            items=[next(w for w in store['stories'][page]['widgets'] if w['name']==name) for name in names]
            self.assertEqual(len({w['states']['matrix'][5] for w in items}),1,'Records must be tabular')

    def test_desktop_tables_clear_trial_notice_at_short_desktop_height(self):
        spec=importlib.util.spec_from_file_location('safe_desktop_builder',ROOT/'dashboard/build_report.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'safe-desktop.fvs';builder.build(target)
            with zipfile.ZipFile(target) as archive:
                store=json.loads(ET.fromstring(archive.read('editor.tpl')).find('DuchampTemplateAttr').get('store'))
        # The native notice occupies the final 90 px in the observed 1366x768
        # desktop viewport. Data widgets must fit above it without font shrinking.
        scale=min(1366/1920,768/1080)
        for page,prefix in [(2,'Registry '),(4,'Operations '),(4,'Payment schedule ')]:
            cells=[w for w in store['stories'][page]['widgets'] if w['name'].startswith(prefix)
                   and isinstance(w['props'].get('value'),str) and w['props']['value'].startswith('=IF(')]
            self.assertTrue(cells)
            for cell in cells:
                bottom=(cell['states']['matrix'][5]+cell['states']['height'])*scale
                self.assertLessEqual(bottom,768-90,cell['name']+' can be obscured by the vendor notice')
                self.assertGreaterEqual(cell['props']['style']['fontSize'],13)

    def test_readable_matrix_uses_fixed_native_rows_with_legible_text(self):
        spec=importlib.util.spec_from_file_location('readable_builder',ROOT/'dashboard/build_report.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'readable.fvs';builder.build(target)
            with zipfile.ZipFile(target) as archive:
                store=json.loads(ET.fromstring(archive.read('editor.tpl')).find('DuchampTemplateAttr').get('store'))
        story=store['stories'][3]
        cells=[w for w in story['widgets'] if w['name'].startswith('Vintage cell ')]
        self.assertEqual(len(cells),36,'The narrow matrix must display six cohorts by six ages')
        metadata=json.loads((ROOT/'validation/native-datasets.json').read_text())
        columns=next(d['columns'] for d in metadata if d['name']=='vintage_matrix_view')
        expected_column=columns.index('cell_label')+1
        reached=set()
        for w in cells:
            self.assertGreaterEqual(w['props']['style']['fontSize'],38)
            expression=w['props']['value']
            match=re.fullmatch(r'=IF\((\d+)<=ROWCOUNT\("vintage_matrix_view"\),VALUE\("vintage_matrix_view",(\d+),(\d+)\),""\)',expression)
            self.assertIsNotNone(match,'Native VALUE rows must be literal; nested dataset expressions do not refresh reliably')
            cohort,offset=map(int,w['name'].split()[-2:])
            expected_row=cohort*6+offset+1
            self.assertEqual(tuple(map(int,match.groups())),(expected_row,expected_column,expected_row))
            reached.add(expected_row)
        self.assertEqual(reached,set(range(1,37)))
        pagers=[a for w in story['widgets'] for g in w.get('widgetEvents',[]) for e in g.get('events',[])
                for a in e.get('actions',[]) if a.get('type')=='widgetLink']
        self.assertEqual(len(pagers),2)
        self.assertTrue(all(a['body']['parameters'][0]['name']=='p_vintage_page' for a in pagers))


if __name__=='__main__':
    unittest.main()
