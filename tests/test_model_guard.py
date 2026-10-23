import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from rd_sweep import DEFAULTS, currents, row, run

class ModelGuardTests(unittest.TestCase):
    def test_old_extrapolation_rejected(self):
        with self.assertRaisesRegex(ValueError,'超出示意模型範圍'):
            currents(-1,-1)
    def test_unmodelled_rf_rejected(self):
        with self.assertRaisesRegex(ValueError,'RF 示意模型'):
            row('rf',1,-2.79,-4.978,46,'FR1')
    def test_no_current_clipping(self):
        r=row('rf',1,-2.65,-4.95,35,'demo')
        self.assertGreater(r['total_idd_a'],3)
        self.assertEqual(r['status'],'total_current_limit')
    def test_pipeline_and_invalid_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            args=argparse.Namespace(**DEFAULTS,rd_config=DEFAULTS,stage='static',output=d/'static.csv')
            _,rows=run(args)
            self.assertEqual(len(rows),25)
            args.stage='rf';args.input=args.output;args.output=d/'rf.csv'
            args.rf_output_dbm=30;args.waveform='demo'
            _,rf=run(args)
            self.assertEqual(len(rf),25)
            args.stage='static';args.main_start=-1;args.main_stop=-1
            args.rd_config=None;args.output=d/'invalid.csv'
            with self.assertRaises(ValueError):
                run(args)
            self.assertFalse(args.output.exists())
    def test_old_csv_explained(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'old.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['mode','stage','status','main_vgs_v','peaking_vgs_v'])
                w.writeheader();w.writerow(dict(mode='simulation',stage='static',status='total_current_limit',main_vgs_v=-1,peaking_vgs_v=-1))
            a=argparse.Namespace(stage='rf',input=p,rf_output_dbm=30,waveform='demo')
            with self.assertRaisesRegex(ValueError,'沒有可用候選點'):
                run(a)
