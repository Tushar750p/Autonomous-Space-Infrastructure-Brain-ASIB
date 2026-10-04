import unittest

from asib.models import NodeStatus
from asib.simulator import Simulator
from asib.validation import SafetyValidator


class TestSafetyValidation(unittest.TestCase):
    def test_healthy_world_is_safe(self):
        sim = Simulator()
        report = SafetyValidator().validate(sim.world)
        self.assertTrue(report.safe)
        self.assertEqual(report.violations, [])

    def test_critical_workload_floor_is_enforced(self):
        sim = Simulator()
        node = sim.world.nodes["orbital-node-01"]
        node.workload = node.critical_workload - 1
        report = SafetyValidator().validate(sim.world)
        self.assertFalse(report.safe)
        self.assertTrue(any(v.invariant == "critical_workload_preservation" for v in report.violations))

    def test_isolated_node_must_be_network_down(self):
        sim = Simulator()
        node = sim.world.nodes["orbital-node-01"]
        node.status = NodeStatus.ISOLATED
        node.network_ok = True
        report = SafetyValidator().validate(sim.world)
        self.assertFalse(report.safe)
        self.assertTrue(any(v.invariant == "isolation_consistency" for v in report.violations))


if __name__ == "__main__":
    unittest.main()
