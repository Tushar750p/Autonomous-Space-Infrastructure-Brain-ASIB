import unittest

from asib.resources import system_resource_report
from asib.simulator import Simulator


class TestResourceReport(unittest.TestCase):
    def test_resource_report_is_bounded_and_complete(self):
        sim = Simulator()
        report = system_resource_report(sim.world)

        self.assertEqual(len(report["nodes"]), 3)
        self.assertGreaterEqual(report["total_free_cpu"], 0)
        self.assertGreaterEqual(report["total_power_reserve_pct"], 0)
        self.assertGreaterEqual(report["min_thermal_headroom_c"], 0)
        self.assertLessEqual(report["network_available_pct"], 100)
        self.assertIn("solar_generation_pct", report)


if __name__ == "__main__":
    unittest.main()
