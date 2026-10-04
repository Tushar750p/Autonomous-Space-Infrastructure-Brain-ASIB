from __future__ import annotations

from dataclasses import dataclass
import json

from .models import AutonomyMode, World


@dataclass(frozen=True)
class ReplayFrame:
    tick: int
    state: dict

    def as_dict(self) -> dict:
        return {"tick": self.tick, "state": self.state}


class StateReplay:
    """JSON-safe state journal for deterministic experiment replay and inspection."""

    def __init__(self):
        self.frames: list[ReplayFrame] = []

    @staticmethod
    def _snapshot(world: World) -> dict:
        return {
            "tick": world.tick,
            "autonomy_mode": world.autonomy_mode.value,
            "comms_delay_s": world.comms_delay_s,
            "global_power_budget_pct": world.global_power_budget_pct,
            "earth_contact_available": world.earth_contact_available,
            "nodes": {
                node_id: {
                    "cpu_capacity": node.cpu_capacity,
                    "cpu_load": node.cpu_load,
                    "temperature_c": node.temperature_c,
                    "power_pct": node.power_pct,
                    "storage_pct": node.storage_pct,
                    "network_ok": node.network_ok,
                    "latency_ms": node.latency_ms,
                    "workload": node.workload,
                    "critical_workload": node.critical_workload,
                    "status": node.status.value,
                }
                for node_id, node in world.nodes.items()
            },
            "links": dict(world.links),
        }

    def capture(self, world: World):
        self.frames.append(ReplayFrame(world.tick, self._snapshot(world)))

    def export(self) -> list[dict]:
        return [frame.as_dict() for frame in self.frames]

    def to_json(self) -> str:
        return json.dumps(self.export(), sort_keys=True, separators=(",", ":"))

    def validate(self) -> bool:
        return all(
            current.tick > previous.tick
            for previous, current in zip(self.frames, self.frames[1:])
        )

    @classmethod
    def from_json(cls, payload: str) -> "StateReplay":
        replay = cls()
        for record in json.loads(payload):
            replay.frames.append(
                ReplayFrame(
                    int(record["tick"]),
                    dict(record["state"]),
                )
            )
        return replay
