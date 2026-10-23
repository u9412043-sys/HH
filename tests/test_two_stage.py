import unittest
from two_stage_idd import row, LIMIT_A

class TwoStageTests(unittest.TestCase):
    def test_total_limit(self):
        r = row('static', 1, -2.6, -4.97)
        self.assertLess(r['main_idd_a'], LIMIT_A)
        self.assertLess(r['peaking_idd_a'], LIMIT_A)
        self.assertEqual(r['status'], 'total_current_limit')

    def test_rf_and_no_fake_aclr(self):
        static = row('static', 1, -2.79, -4.978)
        rf = row('rf', 1, -2.79, -4.978, 30, 'demo')
        self.assertGreater(rf['total_idd_a'], static['total_idd_a'])
        self.assertEqual(rf['aclr_lower_dbc'], '')
