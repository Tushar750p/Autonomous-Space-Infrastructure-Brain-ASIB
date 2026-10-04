import unittest

from asib.mission import MissionEvaluator
from asib.predictor import RiskPredictor
from asib.simulator import Simulator


class TestMissionMetrics(unittest.TestCase):
    def test_mission_reports_service_and_network_health(self):
        sim = Simulator()
        result = MissionEvaluator().evaluate(sim.world)

        self.assertIn("critical_service_pct", result)
        self.assertIn("network_health_pct", result)
        self.assertEqual(result["critical_service_pct"], 100.0)
        self.assertEqual(result["network_health_pct"], 100.0)

    def test_isolated_node_reduces_network_health(self):
        sim = Simulator()
        sim.inject_network_failure("orbital-node-03")
        result = MissionEvaluator().evaluate(sim.world)
        self.assertLess(result["network_health_pct"], 100.0)


class TestEnvironmentRisk(unittest.TestCase):
    def test_eclipse_adds_power_risk_context(self):
        sim = Simulator()
        node = sim.world.nodes["orbital-node-01"]
        node.power_pct = 40

        sim.world.environment.phase_deg = 120
        risks = RiskPredictor().predict(sim.world)

        target = next(risk for risk in risks if risk.node_id == node.node_id)
        self.assertIn("eclipse reducing available solar input", target.reasons)


if __name__ == "__main__":
    unittest.main()
