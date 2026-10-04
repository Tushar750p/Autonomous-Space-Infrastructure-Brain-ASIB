import unittest

from asib.engine import ASIBBrain
from asib.memory import InfrastructureMemory
from asib.mission import MissionEvaluator
from asib.predictor import RiskPredictor
from asib.simulator import Simulator


class TestASIBAdvanced(unittest.TestCase):
    def test_compound_scenario_creates_recovery_memory(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 96)
        sim.inject_power_failure("orbital-node-02", 20)
        sim.inject_network_failure("orbital-node-03")
        sim.world.nodes["orbital-node-03"].critical_workload = 0

        brain = ASIBBrain()
        brain.step(sim.world)

        memory = InfrastructureMemory(sim.world)
        self.assertGreaterEqual(len(sim.world.memory), 3)
        self.assertGreater(memory.summary().get("action", 0), 0)

    def test_predictor_prioritizes_active_fault(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 100)
        risks = RiskPredictor().predict(sim.world)
        self.assertEqual(risks[0].node_id, "orbital-node-01")
        self.assertGreater(risks[0].score, 30)

    def test_mission_score_is_bounded(self):
        sim = Simulator()
        score = MissionEvaluator().evaluate(sim.world)
        self.assertGreaterEqual(score["score"], 0)
        self.assertLessEqual(score["score"], 100)

    def test_memory_query(self):
        sim = Simulator()
        sim.inject_power_failure("orbital-node-01", 12)
        ASIBBrain().step(sim.world)
        memory = InfrastructureMemory(sim.world)
        self.assertGreaterEqual(len(memory.similar("critical", "orbital-node-01")), 1)


if __name__ == "__main__":
    unittest.main()
