import unittest

from asib.experiments import run_experiment_suite


class TestExperiments(unittest.TestCase):
    def test_suite_is_deterministic_and_complete(self):
        first = run_experiment_suite(3)
        second = run_experiment_suite(3)

        self.assertEqual(first, second)
        self.assertTrue(first["deterministic"])
        self.assertEqual(len(first["scenarios"]), 9)
        self.assertIn("compound", {item["scenario"] for item in first["scenarios"]})


if __name__ == "__main__":
    unittest.main()
