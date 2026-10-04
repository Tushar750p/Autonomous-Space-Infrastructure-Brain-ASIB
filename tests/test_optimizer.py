import unittest

from asib.engine import ASIBBrain
from asib.models import Action
from asib.planner import Plan
from asib.simulator import Simulator


class TestPlanOptimization(unittest.TestCase):
    def test_optimizer_is_recorded_and_keeps_safe_execution(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 92.0)
        events = ASIBBrain().step(sim.world)

        decision = sim.world.decision_log[-1]
        self.assertIn("optimization", decision)
        self.assertTrue(decision["optimization"]["enabled"])
        self.assertTrue(events)
        self.assertGreaterEqual(sim.world.nodes["orbital-node-01"].workload,
                                sim.world.nodes["orbital-node-01"].critical_workload)

    def test_optimizer_generates_bounded_variants(self):
        from asib.counterfactual import CounterfactualEvaluator
        from asib.action_executor import ActionExecutor
        from asib.policy import SafetyPolicy
        from asib.validation import SafetyValidator
        from asib.optimizer import ConstrainedPlanOptimizer

        sim = Simulator()
        optimizer = ConstrainedPlanOptimizer(
            CounterfactualEvaluator(ActionExecutor(SafetyPolicy(), SafetyValidator()))
        )
        plan = Plan([
            Action("migrate", "orbital-node-01", "orbital-node-03", 40.0, "test"),
        ], ["test"])

        variants = optimizer._variants(plan)
        self.assertEqual(len(variants), 4)
        self.assertTrue(all(0 < action.amount <= 40 for p in variants[1:] for action in p.actions))


if __name__ == "__main__":
    unittest.main()
