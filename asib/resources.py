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
