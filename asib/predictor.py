from dataclasses import dataclass
from .models import World


@dataclass
class Risk:
    node_id: str
    score: float
    reasons: list[str]


class RiskPredictor:
    """Transparent heuristic predictor; designed for later learned models."""

    def predict(self, world: World) -> list[Risk]:
        risks: list[Risk] = []
        for node in world.nodes.values():
            score = 0.0
            reasons: list[str] = []

            if node.temperature_c >= 70:
                score += min(40.0, (node.temperature_c - 65.0) * 1.2)
                reasons.append("thermal margin narrowing")
            if node.power_pct <= 30:
                score += min(35.0, (30.0 - node.power_pct) * 1.5)
                reasons.append("power reserve low")
            if node.cpu_load >= 80:
                score += 20.0
                reasons.append("compute saturation")
            if not node.network_ok:
                score += 30.0
                reasons.append("network unavailable")
            if node.latency_ms > 500:
                score += min(15.0, node.latency_ms / 100.0)
                reasons.append("high communication latency")

            risks.append(Risk(node.node_id, min(100.0, round(score, 2)), reasons))

        return sorted(risks, key=lambda r: r.score, reverse=True)
