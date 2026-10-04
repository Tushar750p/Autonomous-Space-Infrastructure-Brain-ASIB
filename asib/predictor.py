from dataclasses import dataclass

from .models import World


@dataclass
class Risk:
    node_id: str
    score: float
    reasons: list[str]
    confidence: float = 0.50
    horizon_ticks: int = 0
    score_low: float = 0.0
    score_high: float = 0.0


class RiskPredictor:
    """Transparent risk predictor with trend analysis and uncertainty bounds."""

    def predict(self, world: World) -> list[Risk]:
        risks: list[Risk] = []

        for node in world.nodes.values():
            score = 0.0
            reasons: list[str] = []
            confidence = 0.50
            horizon = 0

            if node.temperature_c >= 70:
                score += min(40.0, (node.temperature_c - 65.0) * 1.2)
                reasons.append("thermal margin narrowing")
            if node.power_pct <= 30:
                score += min(35.0, (30.0 - node.power_pct) * 1.5)
                reasons.append("power reserve low")

            eclipse_change_ticks = world.environment.ticks_until_eclipse_change()
            if world.environment.in_eclipse:
                if node.power_pct <= 50:
                    score += 8.0
                    reasons.append("eclipse reducing available solar input")
                confidence += 0.05
            elif eclipse_change_ticks <= 1 and node.power_pct <= 50:
                score += 5.0
                reasons.append("eclipse transition imminent")
                confidence += 0.05

            if node.cpu_load >= 80:
                score += 20.0
                reasons.append("compute saturation")
            if node.storage_pct >= 80:
                score += min(15.0, (node.storage_pct - 75.0) * 0.6)
                reasons.append("storage headroom low")
            if not node.network_ok:
                score += 30.0
                reasons.append("network unavailable")
            if node.latency_ms > 500:
                score += min(15.0, node.latency_ms / 100.0)
                reasons.append("high communication latency")

            history = world.telemetry.get(node.node_id, [])
            if len(history) >= 3:
                previous = history[-3]
                current = history[-1]
                dt = max(1, current.tick - previous.tick)
                temp_rate = (current.temperature_c - previous.temperature_c) / dt
                power_rate = (current.power_pct - previous.power_pct) / dt

                if temp_rate > 0.5 and node.temperature_c < 85:
                    score += min(20.0, temp_rate * 8.0)
                    reasons.append(f"temperature rising {temp_rate:.2f} C/tick")
                    confidence += 0.15
                    horizon = max(
                        horizon,
                        int(max(1, (85 - node.temperature_c) / temp_rate)),
                    )

                if power_rate < -1.0 and node.power_pct > 15:
                    score += min(15.0, abs(power_rate) * 4.0)
                    reasons.append(f"power reserve falling {abs(power_rate):.2f}%/tick")
                    confidence += 0.10
                    horizon = max(
                        horizon,
                        int(max(1, (node.power_pct - 15) / abs(power_rate))),
                    )

            score = min(100.0, round(score, 2))
            confidence = min(0.95, round(confidence, 2))

            # Confidence becomes a bounded score interval instead of a decorative
            # scalar. Higher uncertainty widens the interval.
            uncertainty = max(2.0, round((1.0 - confidence) * 28.0, 2))
            score_low = max(0.0, round(score - uncertainty, 2))
            score_high = min(100.0, round(score + uncertainty, 2))

            risks.append(Risk(
                node.node_id,
                score,
                reasons,
                confidence,
                horizon,
                score_low,
                score_high,
            ))

        return sorted(risks, key=lambda r: (r.score_high, r.score), reverse=True)
