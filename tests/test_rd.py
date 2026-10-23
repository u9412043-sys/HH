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
