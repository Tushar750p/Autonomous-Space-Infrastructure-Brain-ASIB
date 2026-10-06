import unittest
from types import SimpleNamespace

from asib.decision_intelligence import DecisionIntelligence
from asib.models import Action


class TestDecisionIntelligence(unittest.TestCase):
    def test_safe_action_gets_explainable_confidence(self):
        shadow = SimpleNamespace(
            accepted=True,
            future_safe=True,
            horizon_ticks=2,
            score_delta=4.5,
        )
        assessment = DecisionIntelligence.assess(
            actions=[Action("migrate", "n1", "n2", 10, knowledge_confidence=0.9)],
            shadow=shadow,
            invariant_safe=True,
            decision_class="act",
            needs_human_review=False,
        ).as_dict()

        self.assertGreaterEqual(assessment["confidence"], 0.70)
        self.assertEqual(assessment["risk_level"], "medium")
        self.assertEqual(assessment["action_count"], 1)
        self.assertTrue(assessment["future_safe"])
        self.assertTrue(any("Counterfactual" in item for item in assessment["evidence"]))

    def test_escalation_is_critical(self):
        shadow = SimpleNamespace(
            accepted=False,
            future_safe=False,
            horizon_ticks=2,
            score_delta=-12.0,
        )
        assessment = DecisionIntelligence.assess(
            actions=[],
            shadow=shadow,
            invariant_safe=False,
            decision_class="escalate",
            needs_human_review=True,
        ).as_dict()

        self.assertEqual(assessment["risk_level"], "critical")
        self.assertLess(assessment["confidence"], 0.50)
        self.assertTrue(any("Human review" in item for item in assessment["evidence"]))


if __name__ == "__main__":
    unittest.main()
