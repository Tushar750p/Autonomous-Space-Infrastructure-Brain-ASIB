from collections import defaultdict
from .models import Event, World


class InfrastructureMemory:
    """Queryable operational memory for repeated recovery patterns."""

    def __init__(self, world: World):
        self.world = world

    def record(self, events: list[Event]):
        self.world.memory.extend(events)

    def similar(self, event_type: str, node_id: str | None = None) -> list[Event]:
        return [
            event for event in self.world.memory
            if event.event_type == event_type and (node_id is None or event.node_id == node_id)
        ]

    def summary(self) -> dict:
        counts = defaultdict(int)
        for event in self.world.memory:
            counts[event.event_type] += 1
        return dict(sorted(counts.items()))
