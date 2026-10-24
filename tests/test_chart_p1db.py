import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from rd_sweep import FIELDS, row, write_static_chart, select_p1db, run

class ChartP1dbTests(unittest.TestCase):
    def test_chart_and_p1db_handoff(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);static=d/'static.csv';measured=d/'measured.csv';selected=d/'selected.csv'
            rows=[row('static',1,-2.79,-4.978),row('static',2,-3,-5)]
            with static.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            chart=write_static_chart(rows,static)
            self.assertIn('panel(\'main\',0,1,2)',chart.read_text())
            with measured.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['main_vgs_v','peaking_vgs_v','p1db_output_dbm']);w.writerows([[-2.79,-4.978,46],[-3,-5,46]])
            best=select_p1db(static,measured,46,.5,selected)
            self.assertEqual(float(best['main_vgs_v']),-3)
            a=argparse.Namespace(stage='rf',input=selected,output=d/'rf.csv',waveform='demo',rf_start=0,rf_stop=50,rf_step=25)
            _,rf=run(a)
            self.assertEqual(len(rf),3)
            self.assertTrue(all(r['main_vgs_v']==-3 for r in rf))
            with self.assertRaisesRegex(ValueError,'沒有符合'):
                select_p1db(static,measured,40,.1,d/'none.csv')
            self.assertFalse((d/'none.csv').exists())
    def test_no_p1db_inferred_from_static(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerow(row('static',1,-3,-5))
            with self.assertRaisesRegex(ValueError,'缺少欄位'):
                select_p1db(p,p,46,.5,Path(d)/'out.csv')
