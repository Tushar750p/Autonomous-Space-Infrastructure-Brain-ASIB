from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResourceReservationBook:
    """Tracks plan-local resource reservations so actions remain jointly feasible."""

    reserved_cpu: dict[str, float]

    @classmethod
    def create(cls) -> "ResourceReservationBook":
        return cls(reserved_cpu={})

    def available_cpu(self, node_id: str, node) -> float:
        return max(0.0, node.free_cpu - self.reserved_cpu.get(node_id, 0.0))

    def reserve_cpu(self, node_id: str, node, amount: float) -> bool:
        if amount <= 0:
            return False
        available = self.available_cpu(node_id, node)
        if amount > available:
            return False
        self.reserved_cpu[node_id] = self.reserved_cpu.get(node_id, 0.0) + amount
        return True

    def snapshot(self) -> dict:
        return {node_id: round(amount, 4) for node_id, amount in self.reserved_cpu.items()}


@dataclass(frozen=True)
class ResourceEnvelope:
    node_id: str
    free_cpu: float
    thermal_headroom_c: float
    power_reserve_pct: float
    network_ok: bool

    @classmethod
    def from_node(cls, node) -> "ResourceEnvelope":
        return cls(
            node_id=node.node_id,
            free_cpu=round(node.free_cpu, 2),
            thermal_headroom_c=round(max(0.0, 85.0 - node.temperature_c), 2),
            power_reserve_pct=round(max(0.0, node.power_pct), 2),
            network_ok=node.network_ok,
        )

    def as_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "free_cpu": self.free_cpu,
            "thermal_headroom_c": self.thermal_headroom_c,
            "power_reserve_pct": self.power_reserve_pct,
            "network_ok": self.network_ok,
        }


def system_resource_report(world) -> dict:
    envelopes = [ResourceEnvelope.from_node(node) for node in world.nodes.values()]
    return {
        "total_free_cpu": round(sum(item.free_cpu for item in envelopes), 2),
        "total_power_reserve_pct": round(sum(item.power_reserve_pct for item in envelopes), 2),
        "min_thermal_headroom_c": round(
            min((item.thermal_headroom_c for item in envelopes), default=0.0), 2
        ),
        "network_available_pct": round(
            100.0 * sum(item.network_ok for item in envelopes) / max(1, len(envelopes)),
            2,
        ),
        "solar_generation_pct": world.environment.solar_generation_pct,
        "eclipse": world.environment.in_eclipse,
        "nodes": [item.as_dict() for item in envelopes],
    }
