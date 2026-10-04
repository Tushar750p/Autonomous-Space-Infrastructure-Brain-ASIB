import unittest

from asib.scorecard import RecoveryScorecardBuilder


class TestRecoveryScorecard(unittest.TestCase):
    def test_scorecard_extracts_detection_recovery_and_action_metrics(self):
        reports = [
            type("R", (), {
                "tick": 1,
                "events": [
                    {"event_type": "critical", "severity": "critical", "message": "fault"},
                    {"event_type": "action", "severity": "info", "message": "migrated"},
                ],
            })(),
            type("R", (), {
                "tick": 3,
                "events": [
                    {"event_type": "human_review", "severity": "warning", "message": "review"},
                ],
            })(),
        ]
        result = RecoveryScorecardBuilder.build(reports, 3)

        self.assertEqual(result.first_detection_tick, 1)
        self.assertEqual(result.recovery_tick, 3)
        self.assertEqual(result.detection_latency_ticks, 1)
        self.assertEqual(result.recovery_latency_ticks, 2)
        self.assertEqual(result.autonomous_actions, 1)
        self.assertEqual(result.human_review_events, 1)


if __name__ == "__main__":
    unittest.main()
