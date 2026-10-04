from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastRecord:
    node_id: str
    forecast_tick: int
    horizon_ticks: int
    probability: float
    outcome: bool | None = None


class ForecastLedger:
    """Tracks prediction outcomes and computes simple forecast calibration metrics."""

    def __init__(self):
        self.pending: list[ForecastRecord] = []
        self.completed: list[ForecastRecord] = []

    def record(self, tick: int, risks):
        for risk in risks:
            horizon = max(1, int(risk.horizon_ticks or 1))
            probability = max(0.0, min(1.0, float(risk.score) / 100.0))
            self.pending.append(
                ForecastRecord(
                    risk.node_id,
                    tick,
                    horizon,
                    round(probability, 4),
                )
            )

    @staticmethod
    def _is_failure(node) -> bool:
        return (
            node.temperature_c >= 85.0
            or node.power_pct <= 15.0
            or not node.network_ok
        )

    def observe_outcomes(self, world):
        remaining: list[ForecastRecord] = []

        for record in self.pending:
            if world.tick - record.forecast_tick < record.horizon_ticks:
                remaining.append(record)
                continue

            node = world.nodes.get(record.node_id)
            outcome = self._is_failure(node) if node is not None else True
            self.completed.append(
                ForecastRecord(
                    record.node_id,
                    record.forecast_tick,
                    record.horizon_ticks,
                    record.probability,
                    outcome,
                )
            )

        self.pending = remaining

    def brier_score(self) -> float | None:
        if not self.completed:
            return None
        return round(
            sum(
                (record.probability - float(bool(record.outcome))) ** 2
                for record in self.completed
            )
            / len(self.completed),
            4,
        )

    def summary(self) -> dict:
        completed = len(self.completed)
        predicted_high = sum(r.probability >= 0.7 for r in self.completed)
        observed_high = sum(bool(r.outcome) for r in self.completed)
        return {
            "pending": len(self.pending),
            "completed": completed,
            "brier_score": self.brier_score(),
            "high_risk_forecasts": predicted_high,
            "high_risk_outcomes": observed_high,
            "forecast_skill_sample_size": completed,
        }

    def export(self) -> dict:
        return {
            "pending": [record.__dict__ for record in self.pending],
            "completed": [record.__dict__ for record in self.completed],
            "summary": self.summary(),
        }
