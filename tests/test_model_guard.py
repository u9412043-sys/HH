import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from rd_sweep import DEFAULTS, currents, row, run

class ModelGuardTests(unittest.TestCase):
    def test_old_extrapolation_rejected(self):
        with self.assertRaisesRegex(ValueError,'超出示意模型範圍'):
            currents(-.9,-1)
    def test_unmodelled_rf_rejected(self):
        with self.assertRaisesRegex(ValueError,'RF 示意模型'):
            row('rf',1,-2.79,-4.978,47,'FR1')
    def test_no_current_clipping(self):
        r=row('rf',1,-1,-1,35,'demo')
        self.assertGreater(r['total_idd_a'],3)
        self.assertEqual(r['status'],'total_current_limit')
    def test_pipeline_and_invalid_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            args=argparse.Namespace(**DEFAULTS,rd_config=DEFAULTS,stage='static',output=d/'static.csv')
            _,rows=run(args)
            self.assertEqual(len(rows),81*181)
            args.stage='rf';args.input=args.output;args.output=d/'rf.csv'
            args.rf_output_dbm=30;args.waveform='demo'
            _,rf=run(args)
            self.assertEqual(len(rf),81*181)
            args.stage='static';args.main_start=-.9;args.main_stop=-.9
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

    def test_bounded_monotonic_full_domain(self):
        import math
        from rd_sweep import axis
        main=[currents(v,-10)[0] for v in axis(-5,-1,.05)]
        peak=[currents(-5,v)[1] for v in axis(-10,-1,.05)]
        self.assertEqual(main,sorted(main))
        self.assertEqual(peak,sorted(peak))
        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1.6 for v in main))
        self.assertTrue(all(math.isfinite(v) and 0 <= v <= .8 for v in peak))
        self.assertLess(sum(currents(-1,-1)),3)

    def test_46_dbm_accepted_and_current_limit_preserved(self):
        r=row('rf',1,-2.79,-4.978,46,'FR1')
        self.assertEqual(r['rf_output_dbm'],46)
        self.assertEqual(r['status'],'total_current_limit')
        self.assertGreater(r['total_idd_a'],3)
