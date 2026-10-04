import unittest

from asib.robustness import run_robustness_suite


class TestRobustness(unittest.TestCase):
    def test_robustness_suite_is_deterministic(self):
        first = run_robustness_suite(ticks=2, trials=2, seed=7)
        second = run_robustness_suite(ticks=2, trials=2, seed=7)

        self.assertEqual(first, second)
        self.assertTrue(first["deterministic"])
        self.assertEqual(len(first["scenarios"]), 9)

        for scenario in first["scenarios"]:
            self.assertLessEqual(scenario["min_final_score"], scenario["mean_final_score"])
            self.assertLessEqual(scenario["mean_final_score"], scenario["max_final_score"])


if __name__ == "__main__":
    unittest.main()
