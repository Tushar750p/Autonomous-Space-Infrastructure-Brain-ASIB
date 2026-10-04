import unittest

from asib.counterfactual import CounterfactualEvaluator
from asib.models import Action
from asib.simulator import Simulator


class TestCounterfactual(unittest.TestCase):
    def test_safe_plan_is_accepted_without_mutating_live_world(self):
        sim = Simulator()
        action = Action(
            "shed",
            "orbital-node-01",
            amount=5,
            reason="counterfactual test",
        )
        before = sim.world.nodes["orbital-node-01"].workload

        report = CounterfactualEvaluator().evaluate(sim.world, [action], "T00001")

        self.assertTrue(report.accepted)
        self.assertEqual(sim.world.nodes["orbital-node-01"].workload, before)
        self.assertEqual(report.executed_actions, 1)

    def test_unsafe_plan_is_rejected(self):
        sim = Simulator()
        sim.world.nodes["orbital-node-02"].temperature_c = 90
        action = Action(
            "migrate",
            "orbital-node-01",
            "orbital-node-02",
            10,
            "unsafe target",
        )

        report = CounterfactualEvaluator().evaluate(sim.world, [action], "T00001")

        self.assertFalse(report.accepted)
        self.assertEqual(report.executed_actions, 0)


if __name__ == "__main__":
    unittest.main()
