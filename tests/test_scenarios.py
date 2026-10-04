import unittest

from asib.scenarios import run_fault_scenario


class TestScenarios(unittest.TestCase):
    def test_eclipse_scenario_returns_environment_and_resources(self):
        result = run_fault_scenario("eclipse")
        self.assertTrue(result["environment"]["in_eclipse"])
        self.assertIn("migration_power_floor_pct", result["resources"])

    def test_eclipse_compound_scenario_keeps_local_autonomy(self):
        result = run_fault_scenario("eclipse-compound")
        self.assertTrue(result["environment"]["in_eclipse"])
        self.assertEqual(result["environment"]["solar_generation_pct"], 0.2)
        self.assertIn(result["mode"], {"normal", "conservation", "safe"})
        self.assertIn("forecast_calibration", result)


if __name__ == "__main__":
    unittest.main()
