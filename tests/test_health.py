import unittest

from asib.health import HealthService
from asib.runtime import ASIBRuntime


class TestHealthService(unittest.TestCase):
    def test_healthy_runtime_reports_ok(self):
        runtime = ASIBRuntime()
        health = HealthService(runtime).snapshot()

        self.assertEqual(health["status"], "ok")
        self.assertTrue(health["safety_invariants"])
        self.assertTrue(health["audit_chain"])
        self.assertTrue(health["replay_journal"])

    def test_health_surfaces_human_review(self):
        runtime = ASIBRuntime()
        node = runtime.world.nodes["orbital-node-01"]
        node.temperature_c = 109.0
        node.critical_workload = node.workload
        runtime.brain.step(runtime.world)

        health = HealthService(runtime).snapshot()

        self.assertEqual(health["status"], "degraded")
        self.assertTrue(health["needs_human_review"])
        self.assertEqual(health["decision_class"], "escalate")

    def test_health_detects_audit_tampering(self):
        runtime = ASIBRuntime()
        runtime.tick()
        runtime.world.audit_ledger.entries[0].payload["mode"] = "tampered"

        health = HealthService(runtime).snapshot()

        self.assertEqual(health["status"], "degraded")
        self.assertFalse(health["audit_chain"])


if __name__ == "__main__":
    unittest.main()
