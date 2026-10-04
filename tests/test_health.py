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

    def test_health_detects_audit_tampering(self):
        runtime = ASIBRuntime()
        runtime.tick()
        runtime.world.audit_ledger.entries[0].payload["mode"] = "tampered"

        health = HealthService(runtime).snapshot()

        self.assertEqual(health["status"], "degraded")
        self.assertFalse(health["audit_chain"])


if __name__ == "__main__":
    unittest.main()
