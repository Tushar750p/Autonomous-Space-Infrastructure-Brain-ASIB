from .models import Action, AutonomyMode, NodeStatus, World


class SafetyPolicy:
    """Conservative guardrails for the Earth-based ASIB simulator."""

    THERMAL_CRITICAL = 85.0
    THERMAL_DEGRADED = 70.0
    POWER_CRITICAL = 15.0
    POWER_LOW = 25.0
    MAX_MIGRATION = 40.0

    def mode_for(self, world: World) -> AutonomyMode:
        critical = any(
            n.temperature_c >= self.THERMAL_CRITICAL or n.power_pct <= self.POWER_CRITICAL
            for n in world.nodes.values()
        )
        degraded = any(
            n.temperature_c >= self.THERMAL_DEGRADED or n.power_pct <= self.POWER_LOW or not n.network_ok
            for n in world.nodes.values()
        )
        if critical:
            return AutonomyMode.SAFE
        if degraded:
            return AutonomyMode.CONSERVATION
        return AutonomyMode.NORMAL

    def allow(self, world: World, action: Action) -> bool:
        if action.amount < 0:
            return False
        if action.action_type == "migrate":
            if action.target_node is None or action.source_node == action.target_node:
                return False
            return 0 < action.amount <= self.MAX_MIGRATION
        if action.action_type == "isolate":
            node = world.nodes[action.source_node]
            return node.critical_workload <= 0 or node.status in {NodeStatus.CRITICAL, NodeStatus.DEGRADED}
        if action.action_type == "shed":
            node = world.nodes[action.source_node]
            return action.amount <= max(0.0, node.workload - node.critical_workload)
        return action.action_type in {"reduce_power"}
