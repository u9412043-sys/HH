import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from rd_sweep import rf_axis, run

class RFSweepTests(unittest.TestCase):
    def test_endpoints_and_descending(self):
        self.assertEqual(rf_axis(argparse.Namespace(rf_start=0,rf_stop=50,rf_step=1)),list(range(51)))
        self.assertEqual(rf_axis(argparse.Namespace(rf_start=50,rf_stop=0,rf_step=25)),[50,25,0])
    def test_bad_power_and_step(self):
        for start,stop,step in [(-1,50,1),(0,51,1),(0,50,0),(0,50,float('nan'))]:
            with self.assertRaises(ValueError):
                rf_axis(argparse.Namespace(rf_start=start,rf_stop=stop,rf_step=step))
    def test_record_events_without_stopping(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'static.csv'
            with source.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['mode','stage','status','main_vgs_v','peaking_vgs_v'])
                w.writeheader()
                for m,p in [(-1,-1),(-5,-10)]:
                    w.writerow(dict(mode='simulation',stage='static',status='simulated',main_vgs_v=m,peaking_vgs_v=p))
            a=argparse.Namespace(stage='rf',input=source,output=Path(d)/'rf.csv',waveform='FR1',rf_start=0,rf_stop=50,rf_step=1)
            _,rows=run(a)
            self.assertEqual(len(rows),102)
            self.assertEqual(rows[-1]['rf_output_dbm'],50)
            self.assertTrue(any(r['status']=='total_current_limit' for r in rows))
            self.assertEqual(rows[51]['main_vgs_v'],-5)
            with a.output.open(encoding='utf-8-sig') as f:
                self.assertEqual(len(list(csv.DictReader(f))),102)
