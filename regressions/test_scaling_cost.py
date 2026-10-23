"""The bounded cost driver preserves exact decisions, inputs and measurements."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import scaling_cost


class ScalingCostControls(unittest.TestCase):
    def test_invalid_sizes_fail_before_creating_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'untouched'
            for field in ('pages', 'blocks', 'repeats'):
                for value in (False, True, 0, -1, 1.5, '1', 100):
                    values = {'pages': 1, 'blocks': 2, 'repeats': 1, field: value}
                    with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                        scaling_cost.run_pair(target, **values)
                    self.assertFalse(target.exists())

    def test_actual_pair_replays_and_retains_both_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            row = scaling_cost.run_pair(Path(directory) / 'pair', 1, blocks=2, repeats=2)
            self.assertEqual(row['dimensions']['blocks'], 2)
            self.assertEqual(row['certificate']['decision'], 'equivalent')
            self.assertEqual(row['canonical_bytes'][0], row['canonical_bytes'][1])
            self.assertEqual([r['order'] for r in row['observations']],
                             [['direct', 'certificate'], ['certificate', 'direct']])
            self.assertGreater(row['certificate_bytes'], 0)
            for observation in row['observations']:
                for name in ('direct', 'certificate'):
                    self.assertGreater(observation['measurements'][name]['wall_seconds'], 0)

    def test_wrong_decision_cannot_become_a_timing_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(scaling_cost, 'timed', return_value=({'decision': 'different'}, {})):
                with self.assertRaisesRegex(RuntimeError, 'decision disagreement'):
                    scaling_cost.run_pair(Path(directory) / 'pair', 1, blocks=1, repeats=1)

    def test_occupied_outputs_are_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'occupied'
            target.mkdir()
            marker = target / 'keep'
            marker.write_text('existing user input', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                scaling_cost.run_pair(target, 1, blocks=1, repeats=1)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'existing user input')

    def test_manuscript_table_uses_actual_numeric_consumers(self):
        row = {'dimensions': {'html_resources': 7}, 'input_bytes': 2048,
               'median_direct_ms': 3.125, 'median_certificate_ms': 8.25,
               'certificate_bytes': 4096}
        table = scaling_cost.table_tex([row])
        self.assertIn('7 & 2.00 & 3.12 & 8.25 & 4.00', table)
        self.assertIn('Direct ms', table)
        self.assertNotIn('149.83', table)


if __name__ == '__main__':
    unittest.main()
