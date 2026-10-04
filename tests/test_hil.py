import unittest

from asib.hil import HardwareInLoopHarness, SimulationHardwareAdapter
from asib.models import Action
from asib.simulator import Simulator


class TestHardwareBoundary(unittest.TestCase):
    def test_simulation_adapter_reads_all_nodes(self):
        sim = Simulator()
        harness = HardwareInLoopHarness(sim.world, SimulationHardwareAdapter())
        readings = harness.observe()
        self.assertEqual(len(readings), 3)

    def test_adapter_rejects_unsafe_migration_target(self):
        sim = Simulator()
        target = sim.world.nodes["orbital-node-02"]
        target.temperature_c = 90
        action = Action(
            "migrate",
            "orbital-node-01",
            "orbital-node-02",
            10,
            "test",
            0,
            1.0,
        )
        result = SimulationHardwareAdapter().apply(sim.world, action, "T00001")
        self.assertFalse(result.accepted)

    def test_harness_applies_safe_shed(self):
        sim = Simulator()
        action = Action("shed", "orbital-node-01", amount=5, reason="test")
        events = HardwareInLoopHarness(sim.world).apply([action], "T00001")
        self.assertTrue(events)
        self.assertLess(sim.world.nodes["orbital-node-01"].workload, 70)


if __name__ == "__main__":
    unittest.main()
