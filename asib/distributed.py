from dataclasses import dataclass
import json

from .comms import CommunicationModel, Message
from .models import Event, World
from .network import NetworkModel


@dataclass(frozen=True)
class KnowledgeEstimate:
    snapshot: dict | None
    age_ticks: int
    confidence: float


class DistributedKnowledge:
    """Delayed, observer-specific state knowledge for distributed planning."""

    def __init__(self, world: World):
        self.world = world
        self.comms = CommunicationModel()
        self.network = NetworkModel()
        self.views: dict[str, dict[str, dict]] = {
            node_id: {} for node_id in world.nodes
        }
        self.last_update: dict[tuple[str, str], int] = {}
        self.pending: list[Message] = []
        self._primed = False

    @staticmethod
    def _snapshot(node) -> dict:
        return {
            "node_id": node.node_id,
            "cpu_capacity": node.cpu_capacity,
            "cpu_load": node.cpu_load,
            "temperature_c": node.temperature_c,
            "power_pct": node.power_pct,
            "network_ok": node.network_ok,
            "latency_ms": node.latency_ms,
            "workload": node.workload,
            "critical_workload": node.critical_workload,
            "status": node.status.value,
        }

    def prime(self):
        """Seed an initial common deployment picture at tick zero."""
        tick = self.world.tick
        for observer_id in self.world.nodes:
            self.views[observer_id] = {
                source_id: self._snapshot(source)
                for source_id, source in self.world.nodes.items()
            }
            for source_id in self.world.nodes:
                self.last_update[(observer_id, source_id)] = tick
        self._primed = True

    def sync(self, world: World) -> list[Event]:
        """Broadcast current node state and apply messages that are now available."""
        if not self._primed:
            self.prime()

        for source_id in world.nodes:
            for destination_id in world.nodes:
                if source_id == destination_id:
                    self.views[destination_id][source_id] = self._snapshot(world.nodes[source_id])
                    self.last_update[(destination_id, source_id)] = world.tick
                    continue
                if not self.network.is_connected(world, source_id, destination_id):
                    continue

                payload = json.dumps({
                    "kind": "state_sync",
                    "source": source_id,
                    "created_tick": world.tick,
                    "snapshot": self._snapshot(world.nodes[source_id]),
                })
                self.pending.append(
                    self.comms.send(world, source_id, destination_id, payload)
                )

        return self.deliver_due(world)

    def deliver_due(self, world: World) -> list[Event]:
        delivered: list[Event] = []
        pending: list[Message] = []

        for message in self.pending:
            event = self.comms.deliver(world, message)
            if event is None:
                pending.append(message)
                continue

            try:
                payload = json.loads(message.payload)
                if payload.get("kind") != "state_sync":
                    continue
                source_id = str(payload["source"])
                destination_id = message.destination
                created_tick = int(payload["created_tick"])
                key = (destination_id, source_id)

                previous_tick = self.last_update.get(key, -1)
                if created_tick >= previous_tick:
                    self.views.setdefault(destination_id, {})[source_id] = payload["snapshot"]
                    self.last_update[key] = created_tick

                delivered.append(Event(
                    world.tick,
                    "knowledge_sync",
                    destination_id,
                    f"State from {source_id} available (age={max(0, world.tick - created_tick)} ticks)",
                    "info",
                ))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                delivered.append(Event(
                    world.tick,
                    "knowledge_error",
                    message.destination,
                    "Malformed state-sync message ignored",
                    "warning",
                ))

        self.pending = pending
        return delivered

    def estimate(self, observer_id: str, target_id: str, world: World) -> KnowledgeEstimate:
        if observer_id == target_id:
            return KnowledgeEstimate(self._snapshot(world.nodes[target_id]), 0, 1.0)

        snapshot = self.views.get(observer_id, {}).get(target_id)
        if snapshot is None:
            return KnowledgeEstimate(None, 999999, 0.0)

        created_tick = self.last_update.get((observer_id, target_id), world.tick)
        age = max(0, world.tick - created_tick)

        confidence = 1.0 / (1.0 + age * 0.75)
        if world.comms_delay_s > 0:
            confidence *= max(0.25, 1.0 / (1.0 + world.comms_delay_s * 0.05))

        return KnowledgeEstimate(
            snapshot=snapshot,
            age_ticks=age,
            confidence=round(max(0.05, min(1.0, confidence)), 3),
        )

    def summary(self, world: World) -> dict:
        known = len(self.last_update)
        max_age = 0
        for created_tick in self.last_update.values():
            max_age = max(max_age, max(0, world.tick - created_tick))
        return {
            "known_state_pairs": known,
            "pending_messages": len(self.pending),
            "max_age_ticks": max_age,
            "comms_delay_s": round(world.comms_delay_s, 2),
        }
