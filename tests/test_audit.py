import unittest

from asib.audit import DecisionLedger
from asib.engine import ASIBBrain
from asib.simulator import Simulator


class TestDecisionLedger(unittest.TestCase):
    def test_brain_adds_verifiable_ledger_entry(self):
        sim = Simulator()
        ASIBBrain().step(sim.world)
        self.assertEqual(len(sim.world.audit_ledger.entries), 1)
        self.assertTrue(sim.world.audit_ledger.verify())

    def test_tampering_is_detected(self):
        ledger = DecisionLedger()
        ledger.append({"trace_id": "T00001", "tick": 1, "mode": "normal"})
        ledger.append({"trace_id": "T00002", "tick": 2, "mode": "safe"})
        self.assertTrue(ledger.verify())
        ledger.entries[0].payload["mode"] = "tampered"
        self.assertFalse(ledger.verify())


if __name__ == "__main__":
    unittest.main()
