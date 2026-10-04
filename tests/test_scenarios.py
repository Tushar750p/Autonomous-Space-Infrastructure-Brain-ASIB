import unittest

from asib.scenarios import run_fault_scenario


class TestScenarios(unittest.TestCase):
    def test_eclipse_scenario_returns_environment_and_resources(self):
        result = run_fault_scenario("eclipse")
        self.assertTrue(result["environment"]["in_eclipse"])
        self.assertIn("migration_power_floor_pct", result["resources"])

    def test_eclipse_compound_scenario_keeps_local_autonomy(self):
        result = run_fault_scenario("eclipse-compound")
        self.assertFalse(result["state"]["orbital-node-02"]["network_ok"] is False and result["mode"] == "normal")
        self.assertIn("forecast_calibration", result)


if __name__ == "__main__":
    unittest.main()
