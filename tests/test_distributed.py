import unittest

from asib.runtime import ASIBRuntime
from asib.distributed import DistributedKnowledge
from asib.simulator import Simulator


class TestDistributedKnowledge(unittest.TestCase):
    def test_knowledge_becomes_stale_until_message_arrives(self):
        sim = Simulator()
        sim.inject_comms_delay(3)
        knowledge = DistributedKnowledge(sim.world)
        knowledge.prime()

        sim.world.tick = 1
        sim.world.nodes["orbital-node-02"].temperature_c = 80
        knowledge.sync(sim.world)

        first = knowledge.estimate("orbital-node-01", "orbital-node-02", sim.world)
        self.assertEqual(first.snapshot["temperature_c"], 48)
        self.assertGreater(first.age_ticks, 0)
        self.assertLess(first.confidence, 1.0)

        sim.world.tick = 4
        knowledge.sync(sim.world)
        current = knowledge.estimate("orbital-node-01", "orbital-node-02", sim.world)
        self.assertEqual(current.snapshot["temperature_c"], 80)

    def test_network_partition_stops_fresh_sync(self):
        sim = Simulator()
        sim.inject_network_partition("orbital-node-02")
        knowledge = DistributedKnowledge(sim.world)
        knowledge.prime()

        sim.world.tick = 1
        sim.world.nodes["orbital-node-02"].temperature_c = 99
        knowledge.sync(sim.world)

        estimate = knowledge.estimate("orbital-node-01", "orbital-node-02", sim.world)
        self.assertEqual(estimate.snapshot["temperature_c"], 48)

    def test_runtime_exposes_knowledge_metrics(self):
        runtime = ASIBRuntime()
        report = runtime.tick()
        self.assertIn("knowledge", report.__dict__)
        self.assertGreaterEqual(report.knowledge["known_state_pairs"], 9)

    def test_stale_candidate_is_not_selected(self):
        sim = Simulator()
        sim.inject_comms_delay(5)
        runtime = ASIBRuntime(sim)
        sim.world.tick = 1
        sim.world.nodes["orbital-node-01"].temperature_c = 92
        sim.world.nodes["orbital-node-02"].temperature_c = 90

        runtime.knowledge.sync(sim.world)
        plan = runtime.brain.planner.plan(sim.world, knowledge=runtime.knowledge)

        self.assertFalse(
            any(
                action.action_type == "migrate" and action.target_node == "orbital-node-02"
                for action in plan.actions
            )
        )


if __name__ == "__main__":
    unittest.main()
