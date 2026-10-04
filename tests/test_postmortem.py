import unittest

from asib.postmortem import PostmortemService
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestPostmortem(unittest.TestCase):
    def test_postmortem_contains_decision_and_mission_context(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 96)
        runtime = ASIBRuntime(sim)
        runtime.tick()

        report = PostmortemService(runtime).generate().as_dict()

        self.assertEqual(report["tick"], runtime.world.tick)
        self.assertIn("mission", report)
        self.assertIn("decision_class", report)
        self.assertIn("audit_valid", report)

    def test_postmortem_surfaces_unresolved_risk(self):
        sim = Simulator()
        sim.inject_power_failure("orbital-node-02", 18)
        runtime = ASIBRuntime(sim)
        runtime.tick()

        report = PostmortemService(runtime).generate()
        self.assertIsInstance(report.unresolved_risks, list)


if __name__ == "__main__":
    unittest.main()
