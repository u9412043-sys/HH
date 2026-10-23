import unittest
from rd_sweep import DEFAULTS, validate_config

class RDTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_config(DEFAULTS)[1],25)
    def test_requested_stop_outside_limits(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,main_stop=-2.64))
    def test_nan(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,main_min=float('nan')))
    def test_reversed_limits(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,main_min=-2.6))
    def test_zero_step(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,peaking_step=0))

class DirectionTests(unittest.TestCase):
    def test_descending(self):
        from rd_sweep import axis
        self.assertEqual(axis(-1,-1.1,.05),[-1,-1.05,-1.1])
    def test_screenshot_ranges(self):
        c=dict(DEFAULTS,main_min=-5,main_max=-1,main_start=-1,main_stop=-5,
               peaking_min=-10,peaking_max=-1,peaking_start=-1,peaking_stop=-10,
               main_step=.05,peaking_step=.05)
        self.assertEqual(validate_config(c)[1],81*181)
    def test_descending_outside_rd(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,main_start=-2.6,main_stop=-2.9))
    def test_below_dac_range(self):
        with self.assertRaises(ValueError):
            validate_config(dict(DEFAULTS,peaking_min=-10.1))
