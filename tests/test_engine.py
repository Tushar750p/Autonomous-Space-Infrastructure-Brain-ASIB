import unittest

from asib.engine import ASIBBrain
from asib.models import NodeStatus
from asib.simulator import Simulator


class TestASIBBrain(unittest.TestCase):
    def test_thermal_and_power_recovery(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01")
        sim.inject_power_failure("orbital-node-01", 18)
        events = ASIBBrain().step(sim.world)
        self.assertTrue(events)
        self.assertLess(sim.world.nodes["orbital-node-01"].workload, 70)
        self.assertGreater(len(sim.world.memory), 0)

    def test_power_stress_changes_mode(self):
        sim = Simulator()
        sim.inject_power_failure("orbital-node-02", 10)
        ASIBBrain().step(sim.world)
        self.assertLess(sim.world.nodes["orbital-node-02"].workload, 55)
        self.assertEqual(sim.world.autonomy_mode.value, "safe")

    def test_network_failure_isolated_when_no_critical_workload(self):
        sim = Simulator()
        node = sim.world.nodes["orbital-node-03"]
        node.critical_workload = 0
        sim.inject_network_failure("orbital-node-03")
        ASIBBrain().step(sim.world)
        self.assertEqual(node.status, NodeStatus.ISOLATED)

    def test_migration_preserves_critical_workload(self):
        sim = Simulator()
        source = sim.world.nodes["orbital-node-01"]
        sim.inject_thermal_failure(source.node_id)
        before_critical = source.critical_workload
        ASIBBrain().step(sim.world)
        self.assertGreaterEqual(source.workload, before_critical)

    def test_comms_delay_is_part_of_world_state(self):
        sim = Simulator()
        sim.inject_comms_delay(18.5)
        self.assertEqual(sim.world.comms_delay_s, 18.5)

    def test_safe_mode_without_action_requests_human_review(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 109)
        sim.world.nodes["orbital-node-01"].critical_workload = sim.world.nodes["orbital-node-01"].workload
        events = ASIBBrain().step(sim.world)

        self.assertTrue(any(event.event_type == "human_review" for event in events))
        self.assertEqual(sim.world.decision_log[-1]["decision_class"], "escalate")


if __name__ == "__main__":
    unittest.main()


    def test_rejected_primary_plan_is_repaired_locally(self):
        sim = Simulator()
        source = sim.world.nodes["orbital-node-01"]
        sim.world.environment.phase_deg = 30.0
        source.temperature_c = 96.0
        for node_id in ("orbital-node-02", "orbital-node-03"):
            sim.world.nodes[node_id].power_pct = 26.0

        events = ASIBBrain().step(sim.world)

        self.assertTrue(any(event.event_type == "shadow_reject" for event in events))
        self.assertTrue(any(event.event_type == "plan_repair" for event in events))
        self.assertEqual(sim.world.decision_log[-1]["decision_class"], "repair")


    def test_rejected_primary_plan_is_repaired_locally(self):
        sim = Simulator()
        source = sim.world.nodes["orbital-node-01"]
        sim.world.environment.phase_deg = 30.0
        source.temperature_c = 96.0
        for node_id in ("orbital-node-02", "orbital-node-03"):
            sim.world.nodes[node_id].power_pct = 26.0

        events = ASIBBrain().step(sim.world)

        self.assertTrue(any(event.event_type == "shadow_reject" for event in events))
        self.assertTrue(any(event.event_type == "plan_repair" for event in events))
        self.assertEqual(sim.world.decision_log[-1]["decision_class"], "repair")


if __name__ == "__main__":
    unittest.main()
