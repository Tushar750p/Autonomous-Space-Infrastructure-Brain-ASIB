from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .action_executor import ActionExecutor
from .models import Action, Event, World
from .policy import SafetyPolicy
from .validation import SafetyValidator


@dataclass(frozen=True)
class HardwareReading:
    node_id: str
    cpu_load: float
    temperature_c: float
    power_pct: float
    network_ok: bool
    timestamp_tick: int


@dataclass(frozen=True)
class ActuationResult:
    accepted: bool
    events: list[Event]
    reason: str = ""


class HardwareAdapter(Protocol):
    """Strict boundary for future HIL adapters; no physical I/O is implemented here."""

    def read(self, world: World) -> list[HardwareReading]:
        ...

    def apply(self, world: World, action: Action, trace_id: str) -> ActuationResult:
        ...


class SimulationHardwareAdapter:
    """Simulation-only adapter used to prove the HIL boundary without device access."""

    def __init__(self):
        self.policy = SafetyPolicy()
        self.validator = SafetyValidator()
        self.executor = ActionExecutor(self.policy, self.validator)

    def read(self, world: World) -> list[HardwareReading]:
        return [
            HardwareReading(
                node_id=node.node_id,
                cpu_load=node.cpu_load,
                temperature_c=node.temperature_c,
                power_pct=node.power_pct,
                network_ok=node.network_ok,
                timestamp_tick=world.tick,
            )
            for node in world.nodes.values()
        ]

    def apply(self, world: World, action: Action, trace_id: str) -> ActuationResult:
        events = self.executor.execute(world, [action], trace_id)
        accepted = any(event.event_type == "action" for event in events) and not any(
            event.event_type in {"blocked_action", "invariant_violation"} for event in events
        )
        return ActuationResult(
            accepted=accepted,
            events=events,
            reason="" if accepted else "safety or execution guard rejected command",
        )


class HardwareInLoopHarness:
    """Reference harness for replacing simulation sensing/actuation later."""

    def __init__(self, world: World, adapter: HardwareAdapter | None = None):
        self.world = world
        self.adapter = adapter or SimulationHardwareAdapter()

    def observe(self) -> list[HardwareReading]:
        return self.adapter.read(self.world)

    def apply(self, actions: list[Action], trace_id: str) -> list[Event]:
        events: list[Event] = []
        for action in actions:
            result = self.adapter.apply(self.world, action, trace_id)
            events.extend(result.events)
        return events
