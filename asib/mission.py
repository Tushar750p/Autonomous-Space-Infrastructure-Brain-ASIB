from dataclasses import dataclass
from .models import World


@dataclass
class MissionObjective:
    name: str
    target: float
    weight: float


class MissionEvaluator:
    """Scores simulated infrastructure while exposing mission-level health metrics."""

    def evaluate(self, world: World) -> dict:
        if not world.nodes:
            return {
                "availability_pct": 0.0,
                "thermal_health_pct": 0.0,
                "power_health_pct": 0.0,
                "critical_service_pct": 0.0,
                "network_health_pct": 0.0,
                "score": 0.0,
            }

        count = len(world.nodes)
        nominal = sum(1 for n in world.nodes.values() if n.status.value == "nominal")
        serviceable = sum(
            1
            for n in world.nodes.values()
            if n.workload + 1e-9 >= n.critical_workload
        )
        network_healthy = sum(1 for n in world.nodes.values() if n.network_ok)

        thermal = sum(
            max(
                0.0,
                min(100.0, 100.0 - max(0.0, n.temperature_c - 40.0) * 1.6),
            )
            for n in world.nodes.values()
        )
        power = sum(n.power_pct for n in world.nodes.values())

        availability = 100.0 * nominal / count
        thermal_health = thermal / count
        power_health = power / count
        critical_service = 100.0 * serviceable / count
        network_health = 100.0 * network_healthy / count

        score = (
            0.35 * availability
            + 0.25 * thermal_health
            + 0.20 * power_health
            + 0.10 * critical_service
            + 0.10 * network_health
        )

        return {
            "availability_pct": round(availability, 2),
            "thermal_health_pct": round(thermal_health, 2),
            "power_health_pct": round(power_health, 2),
            "critical_service_pct": round(critical_service, 2),
            "network_health_pct": round(network_health, 2),
            "score": round(max(0.0, min(100.0, score)), 2),
        }
