import unittest
from idd_sweep import points, sweep


class SweepTests(unittest.TestCase):
    def test_decimal_endpoints(self):
        self.assertEqual(points(-2.89, -2.69, .05), [-2.89, -2.84, -2.79, -2.74, -2.69])

    def test_limit_stops_before_next_bias(self):
        rows = list(sweep([-2.79, -2.0, -1.0], [-4.978], 3))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]['status'], 'current_limit')

    def test_invalid_step(self):
        with self.assertRaises(ValueError):
            points(-3, -2, 0)

    def test_no_fake_aclr(self):
        row = next(sweep([-2.79], [-4.978], 3))
        self.assertEqual(row['aclr_lower_db'], '')
        self.assertAlmostEqual(row['total_idd_a'], 1.55)
