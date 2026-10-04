from dataclasses import dataclass
from .models import World


@dataclass
class MissionObjective:
    name: str
    target: float
    weight: float


class MissionEvaluator:
    """Scores the simulated infrastructure without hiding the underlying metrics."""

    def evaluate(self, world: World) -> dict:
        if not world.nodes:
            return {"availability_pct": 0.0, "thermal_health_pct": 0.0, "power_health_pct": 0.0, "score": 0.0}

        nominal = sum(1 for n in world.nodes.values() if n.status.value == "nominal")
        thermal = sum(max(0.0, min(100.0, 100.0 - max(0.0, n.temperature_c - 40.0) * 1.6)) for n in world.nodes.values())
        power = sum(n.power_pct for n in world.nodes.values())
        count = len(world.nodes)

        availability = 100.0 * nominal / count
        thermal_health = thermal / count
        power_health = power / count

        score = 0.45 * availability + 0.30 * thermal_health + 0.25 * power_health
        return {
            "availability_pct": round(availability, 2),
            "thermal_health_pct": round(thermal_health, 2),
            "power_health_pct": round(power_health, 2),
            "score": round(score, 2),
        }
