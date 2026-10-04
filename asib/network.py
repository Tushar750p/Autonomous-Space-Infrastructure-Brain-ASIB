from dataclasses import dataclass

from .models import Event, World


@dataclass
class Link:
    a: str
    b: str
    up: bool = True
    latency_ms: float = 40.0


class NetworkModel:
    """Deterministic node-to-node connectivity model for the Earth testbed."""

    def _key(self, a: str, b: str) -> str:
        return "|".join(sorted((a, b)))

    def ensure_full_mesh(self, world: World):
        node_ids = list(world.nodes)
        for i, a in enumerate(node_ids):
            for b in node_ids[i + 1:]:
                world.links.setdefault(self._key(a, b), True)

    def is_connected(self, world: World, a: str, b: str) -> bool:
        if a == b:
            return True
        self.ensure_full_mesh(world)
        return world.links.get(self._key(a, b), True) and world.nodes[a].network_ok and world.nodes[b].network_ok

    def set_link(self, world: World, a: str, b: str, up: bool) -> Event:
        self.ensure_full_mesh(world)
        world.links[self._key(a, b)] = up
        return Event(
            world.tick,
            "network_change",
            a,
            f"Link {a}<->{b} {'up' if up else 'down'}",
            "info" if up else "warning",
        )

    def partition_node(self, world: World, node_id: str) -> list[Event]:
        self.ensure_full_mesh(world)
        events = []
        for other in world.nodes:
            if other == node_id:
                continue
            self.set_link(world, node_id, other, False)
            events.append(Event(world.tick, "network_partition", node_id,
                                f"Partitioned from {other}", "warning"))
        return events
