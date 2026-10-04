from .models import Action, Event, NodeStatus, World
from .planner import MultiNodePlanner
from .policy import SafetyPolicy


class ASIBBrain:
    """Autonomous controller for the ASIB Earth-based digital twin."""

    def __init__(self):
        self.policy = SafetyPolicy()
        self.planner = MultiNodePlanner(self.policy)

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
        return events

    def execute(self, world: World, actions: list[Action]) -> list[Event]:
        events: list[Event] = []
        for action in actions:
            source = world.nodes[action.source_node]
            if not self.policy.allow(world, action):
                events.append(Event(world.tick, "blocked_action", source.node_id,
                                    f"Blocked unsafe action: {action.action_type}", "critical", action.action_type))
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
                                        f"Migrated {amount:.1f} workload to {target.node_id}", action=action.action_type))
            elif action.action_type == "shed":
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
                source.workload -= amount
                source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                events.append(Event(world.tick, "action", source.node_id,
                                    f"Shed {amount:.1f} non-critical workload", action=action.action_type))
            elif action.action_type == "reduce_power":
                amount = min(action.amount, max(0.0, source.workload - source.critical_workload))
                source.workload -= amount
                source.cpu_load = max(source.critical_workload, source.cpu_load - amount)
                events.append(Event(world.tick, "action", source.node_id,
                                    f"Reduced load by {amount:.1f} for power conservation", action=action.action_type))
            elif action.action_type == "isolate":
                source.status = NodeStatus.ISOLATED
                events.append(Event(world.tick, "action", source.node_id,
                                    "Node isolated from coordination", action=action.action_type))
        return events

    def verify(self, world: World, actions: list[Action]) -> list[Event]:
        results: list[Event] = []
        for action in actions:
            node = world.nodes[action.source_node]
            safe = node.temperature_c < self.policy.THERMAL_CRITICAL and node.power_pct > self.policy.POWER_CRITICAL
            if action.action_type == "migrate" and action.target_node:
                safe = safe and world.nodes[action.target_node].cpu_load <= 100.0
            status = "verified" if safe else "not_verified"
            results.append(Event(world.tick, "verification", node.node_id,
                                 f"Action verification: {status}", "info" if safe else "critical",
                                 action.action_type))
        return results

    def step(self, world: World) -> list[Event]:
        observed = self.observe(world)
        plan = self.planner.plan(world)
        actions = self.execute(world, plan.actions)
        verified = self.verify(world, actions)
        history = observed + actions + verified
        world.memory.extend(history)
        return history
