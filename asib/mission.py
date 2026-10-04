from __future__ import annotations

from dataclasses import dataclass
from .models import World


@dataclass(frozen=True)
class MissionObjective:
    name: str
    target: float
    weight: float


@dataclass(frozen=True)
class MissionProfile:
    """Mission-level scoring profile with validated objective weights."""

    name: str = "default"
    availability_weight: float = 0.35
    thermal_weight: float = 0.25
    power_weight: float = 0.20
    critical_service_weight: float = 0.10
    network_weight: float = 0.10

    def normalized(self) -> "MissionProfile":
        weights = [
            self.availability_weight,
            self.thermal_weight,
            self.power_weight,
            self.critical_service_weight,
            self.network_weight,
        ]
        if any(weight < 0 for weight in weights):
            raise ValueError("Mission weights must be non-negative")
        total = sum(weights)
        if total <= 0:
            raise ValueError("Mission weights must sum to a positive value")
        return MissionProfile(
            name=self.name,
            availability_weight=self.availability_weight / total,
            thermal_weight=self.thermal_weight / total,
            power_weight=self.power_weight / total,
            critical_service_weight=self.critical_service_weight / total,
            network_weight=self.network_weight / total,
        )


class MissionEvaluator:
    """Scores simulated infrastructure with explicit, configurable mission priorities."""

    def __init__(self, profile: MissionProfile | None = None):
        self.profile = (profile or MissionProfile()).normalized()

    def evaluate(self, world: World) -> dict:
        if not world.nodes:
            return {
                "profile": self.profile.name,
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
        power = sum(max(0.0, min(100.0, n.power_pct)) for n in world.nodes.values())

        availability = 100.0 * nominal / count
        thermal_health = thermal / count
        power_health = power / count
        critical_service = 100.0 * serviceable / count
        network_health = 100.0 * network_healthy / count

        p = self.profile
        score = (
            p.availability_weight * availability
            + p.thermal_weight * thermal_health
            + p.power_weight * power_health
            + p.critical_service_weight * critical_service
            + p.network_weight * network_health
        )

        return {
            "profile": self.profile.name,
            "availability_pct": round(availability, 2),
            "thermal_health_pct": round(thermal_health, 2),
            "power_health_pct": round(power_health, 2),
            "critical_service_pct": round(critical_service, 2),
            "network_health_pct": round(network_health, 2),
            "score": round(max(0.0, min(100.0, score)), 2),
        }
