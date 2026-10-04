import unittest

from types import SimpleNamespace

from asib.calibration import ForecastLedger


class TestForecastLedger(unittest.TestCase):
    def test_forecast_completes_at_horizon_and_brier_score_is_bounded(self):
        ledger = ForecastLedger()
        risk = SimpleNamespace(node_id="n1", score=80.0, horizon_ticks=2)
        ledger.record(1, [risk])

        world = SimpleNamespace(
            tick=2,
            nodes={"n1": SimpleNamespace(temperature_c=50, power_pct=80, network_ok=True)},
        )
        ledger.observe_outcomes(world)
        self.assertEqual(ledger.summary()["completed"], 0)

        world.tick = 3
        ledger.observe_outcomes(world)
        self.assertEqual(ledger.summary()["completed"], 1)
        self.assertGreaterEqual(ledger.brier_score(), 0.0)
        self.assertLessEqual(ledger.brier_score(), 1.0)

    def test_failed_node_counts_as_observed_risk(self):
        ledger = ForecastLedger()
        risk = SimpleNamespace(node_id="n1", score=75.0, horizon_ticks=1)
        ledger.record(1, [risk])

        world = SimpleNamespace(
            tick=2,
            nodes={"n1": SimpleNamespace(temperature_c=90, power_pct=80, network_ok=True)},
        )
        ledger.observe_outcomes(world)

        summary = ledger.summary()
        self.assertEqual(summary["high_risk_outcomes"], 1)
        self.assertEqual(summary["completed"], 1)


if __name__ == "__main__":
    unittest.main()
