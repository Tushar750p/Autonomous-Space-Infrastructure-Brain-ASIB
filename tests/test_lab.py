import unittest

from asib.lab import run_research_lab


class TestResearchLab(unittest.TestCase):
    def test_lab_is_deterministic_and_complete(self):
        first = run_research_lab(ticks=1, robustness_trials=1, seed=11)
        second = run_research_lab(ticks=1, robustness_trials=1, seed=11)

        self.assertEqual(first, second)
        self.assertEqual(set(first), {"version", "selftest", "benchmark", "experiments", "robustness"})
        self.assertTrue(first["selftest"]["passed"])


if __name__ == "__main__":
    unittest.main()
