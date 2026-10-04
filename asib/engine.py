from .models import Action, Event, NodeStatus, World
from .planner import MultiNodePlanner
from .policy import SafetyPolicy
from .validation import SafetyValidator


class ASIBBrain:
    """Autonomous controller for the ASIB Earth-based digital twin."""

    def __init__(self):
        self.policy = SafetyPolicy()
        self.planner = MultiNodePlanner(self.policy)
        self.validator = SafetyValidator()

    def observe(self, world: World) -> list[Event]:
        events: list[Event] = []
        for node in world.nodes.values():
            if node.temperature_c >= self.policy.THERMAL_CRITICAL or node.power_pct <= self.policy.POWER_CRITICAL:
                node.status = NodeStatus.CRITICAL
                events.append(Event(world.tick, "critical", node.node_id,
                                    "Critical infrastructure condition detected", "critical"))
            elif node.temperature_c >= self.policy.THERMAL_DEGRADED or node.power_pct <= self.policy.POWER_LOW or not node.network_ok:
                node.status = NodeStatus.DEGRADED
                events.append(Event(world.tick, "degradation", node.node_id,
                                    "Infrastructure degradation detected", "warning"))
            elif node.status != NodeStatus.ISOLATED:
                node.status = NodeStatus.NOMINAL
        world.autonomy_mode = self.policy.mode_for(world)
        if not world.earth_contact_available:
            events.append(Event(
                world.tick,
                "earth_contact",
                "earth",
                "Earth contact unavailable; continuing local autonomy",
                "warning",
            ))
        return events

    def execute(self, world: World, actions: list[Action], trace_id: str) -> list[Event]:
        events: list[Event] = []
        for action in actions:
            source = world.nodes[action.source_node]
            if not self.policy.allow(world, action):
                events.append(Event(world.tick, "blocked_action", source.node_id,
                                    f"Blocked unsafe action: {action.action_type}", "critical",
                                    action.action_type, trace_id))
                continue

            if action.action_type == "migrate" and action.target_node:
                target = world.nodes[action.target_node]
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload), target.free_cpu)
                if amount > 0:
                    source.workload -= amount
                    source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                    target.workload += amount
                    target.cpu_load = min(100.0, target.cpu_load + amount)
                    events.append(Event(world.tick, "action", source.node_id,
                                        f"Migrated {amount:.1f} workload to {target.node_id}", action=action.action_type,
                                        trace_id=trace_id))
            elif action.action_type == "shed":
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
                source.workload -= amount
                source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                events.append(Event(world.tick, "action", source.node_id,
                                    f"Shed {amount:.1f} non-critical workload", action=action.action_type,
                                    trace_id=trace_id))
            elif action.action_type == "reduce_power":
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
                source.workload -= amount
                source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                events.append(Event(world.tick, "action", source.node_id,
                                    f"Reduced load by {amount:.1f} for power conservation", action=action.action_type,
                                    trace_id=trace_id))
            elif action.action_type == "isolate":
                source.network_ok = False
                source.status = NodeStatus.ISOLATED
                events.append(Event(world.tick, "action", source.node_id,
                                    "Node isolated from coordination", action=action.action_type,
                                    trace_id=trace_id))

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

    def verify(self, world: World, actions: list[Action], execution_events: list[Event], trace_id: str) -> list[Event]:
        results: list[Event] = []
        executed_types = {(event.node_id, event.action) for event in execution_events if event.event_type == "action"}
        invariant_report = self.validator.validate(world)

        for action in actions:
            if (action.source_node, action.action_type) not in executed_types:
                results.append(Event(world.tick, "verification", action.source_node,
                                     "Action not verified because execution did not occur",
                                     "warning", action.action_type, trace_id))
                continue

            node = world.nodes[action.source_node]
            safe = node.temperature_c < self.policy.THERMAL_CRITICAL and node.power_pct > self.policy.POWER_CRITICAL
            if action.action_type == "migrate" and action.target_node:
                safe = safe and world.nodes[action.target_node].cpu_load <= 100.0
            safe = safe and invariant_report.safe

            status = "verified" if safe else "not_verified"
            results.append(Event(world.tick, "verification", node.node_id,
                                 f"Action verification: {status}",
                                 "info" if safe else "critical",
                                 action.action_type, trace_id))
        return results

    def step(self, world: World, knowledge=None) -> list[Event]:
        trace_id = f"T{world.tick + 1:05d}"
        observed = self.observe(world)
        plan = self.planner.plan(world, knowledge=knowledge)
        execution_events = self.execute(world, plan.actions, trace_id)
        verified = self.verify(world, plan.actions, execution_events, trace_id)

        history = observed + execution_events + verified
        world.memory.extend(history)
        decision = {
            "trace_id": trace_id,
            "tick": world.tick,
            "mode": world.autonomy_mode.value,
            "rationale": plan.rationale,
            "actions": [action.__dict__ for action in plan.actions],
            "executed": [event.message for event in execution_events],
            "verified": [event.message for event in verified],
            "invariants_safe": self.validator.validate(world).safe,
        }
        world.decision_log.append(decision)
        world.audit_ledger.append(decision)
        return history
