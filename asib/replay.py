from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .models import World


@dataclass(frozen=True)
class ReplayFrame:
    tick: int
    state: dict
    previous_digest: str = ""
    digest: str = ""

    def as_dict(self) -> dict:
        return {
            "tick": self.tick,
            "state": self.state,
            "previous_digest": self.previous_digest,
            "digest": self.digest,
        }


class StateReplay:
    """Tamper-evident JSON-safe state journal for deterministic replay."""

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
            "environment": world.environment.snapshot(),
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

    @staticmethod
    def _digest(tick: int, state: dict, previous_digest: str) -> str:
        canonical = json.dumps(
            {
                "tick": tick,
                "state": state,
                "previous_digest": previous_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def capture(self, world: World):
        previous = self.frames[-1].digest if self.frames else ""
        state = self._snapshot(world)
        digest = self._digest(world.tick, state, previous)
        self.frames.append(ReplayFrame(world.tick, state, previous, digest))

    def export(self) -> list[dict]:
        return [frame.as_dict() for frame in self.frames]

    def to_json(self) -> str:
        return json.dumps(self.export(), sort_keys=True, separators=(",", ":"))

    def validate(self) -> bool:
        previous_tick = None
        previous_digest = ""
        for frame in self.frames:
            if previous_tick is not None and frame.tick <= previous_tick:
                return False
            if frame.previous_digest != previous_digest:
                return False
            expected = self._digest(frame.tick, frame.state, frame.previous_digest)
            if frame.digest != expected:
                return False
            previous_tick = frame.tick
            previous_digest = frame.digest
        return True

    @classmethod
    def from_json(cls, payload: str) -> "StateReplay":
        replay = cls()
        for record in json.loads(payload):
            tick = int(record["tick"])
            state = dict(record["state"])
            previous_digest = str(record.get("previous_digest", ""))
            digest = str(record.get("digest", ""))
            if not digest:
                digest = cls._digest(tick, state, previous_digest)
            replay.frames.append(ReplayFrame(tick, state, previous_digest, digest))
        return replay
