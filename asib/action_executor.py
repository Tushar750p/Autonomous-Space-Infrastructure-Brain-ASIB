from __future__ import annotations

from .models import Action, Event, NodeStatus, World
from .policy import SafetyPolicy
from .validation import SafetyValidator


class ActionExecutor:
    """Single execution path shared by the brain, shadow tests and HIL adapter."""

    def __init__(
        self,
        policy: SafetyPolicy | None = None,
        validator: SafetyValidator | None = None,
    ):
        self.policy = policy or SafetyPolicy()
        self.validator = validator or SafetyValidator()

    def execute(self, world: World, actions: list[Action], trace_id: str) -> list[Event]:
        events: list[Event] = []

        for action in actions:
            source = world.nodes.get(action.source_node)
            if source is None or not self.policy.allow(world, action):
                events.append(Event(
                    world.tick,
                    "blocked_action",
                    action.source_node,
                    f"Blocked unsafe action: {action.action_type}",
                    "critical",
                    action.action_type,
                    trace_id,
                ))
                continue

            if action.action_type == "migrate" and action.target_node:
                target = world.nodes[action.target_node]
                amount = min(
                    action.amount,
                    max(0.0, source.workload - source.critical_workload),
                    target.free_cpu,
                )
                if amount > 0:
                    source.workload -= amount
                    source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                    target.workload += amount
                    target.cpu_load = min(100.0, target.cpu_load + amount)
                    events.append(Event(
                        world.tick,
                        "action",
                        source.node_id,
                        f"Migrated {amount:.1f} workload to {target.node_id}",
                        action=action.action_type,
                        trace_id=trace_id,
                    ))

            elif action.action_type in {"shed", "reduce_power"}:
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
                source.workload -= amount
                source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                verb = "Shed" if action.action_type == "shed" else "Reduced load"
                events.append(Event(
                    world.tick,
                    "action",
                    source.node_id,
                    f"{verb} {amount:.1f} workload for resource protection",
                    action=action.action_type,
                    trace_id=trace_id,
                ))

            elif action.action_type == "isolate":
                source.network_ok = False
                source.status = NodeStatus.ISOLATED
                events.append(Event(
                    world.tick,
                    "action",
                    source.node_id,
                    "Node isolated from coordination",
                    action=action.action_type,
                    trace_id=trace_id,
                ))

        report = self.validator.validate(world)
        for violation in report.violations:
            events.append(Event(
                world.tick,
                "invariant_violation",
                violation.node_id,
                f"{violation.invariant}: {violation.message}",
                "critical",
                trace_id=trace_id,
            ))

        return events
