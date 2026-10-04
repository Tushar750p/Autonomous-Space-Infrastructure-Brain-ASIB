from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
        if not self.policy.allow(world, action):
            return ActuationResult(
                accepted=False,
                events=[Event(
                    world.tick,
                    "adapter_reject",
                    action.source_node,
                    f"Adapter rejected unsafe action: {action.action_type}",
                    "critical",
                    action.action_type,
                    trace_id,
                )],
                reason="safety policy rejected command",
            )

        # This adapter deliberately supports only the simulator's non-physical
        # state mutations. A future physical adapter must be implemented
        # separately and independently qualified.
        source = world.nodes[action.source_node]
        if action.action_type == "shed":
            amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
            source.workload -= amount
            source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
        elif action.action_type == "reduce_power":
            amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
            source.workload -= amount
            source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
        elif action.action_type == "migrate" and action.target_node:
            target = world.nodes[action.target_node]
            amount = min(action.amount, max(0.0, source.workload - source.critical_workload), target.free_cpu)
            if amount <= 0:
                return ActuationResult(False, [], "no transferable workload")
            source.workload -= amount
            source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
            target.workload += amount
            target.cpu_load = min(100.0, target.cpu_load + amount)
        elif action.action_type == "isolate":
            source.network_ok = False

        safe = self.validator.validate(world).safe
        event = Event(
            world.tick,
            "adapter_apply",
            source.node_id,
            f"Simulation adapter {'accepted' if safe else 'applied then flagged'} {action.action_type}",
            "info" if safe else "critical",
            action.action_type,
            trace_id,
        )
        return ActuationResult(safe, [event], "" if safe else "post-action invariant violation")


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
