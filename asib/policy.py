from .models import Action, AutonomyMode, NodeStatus, World


class SafetyPolicy:
    """Conservative guardrails for the Earth-based ASIB simulator."""

    THERMAL_CRITICAL = 85.0
    THERMAL_DEGRADED = 70.0
    POWER_CRITICAL = 15.0
    POWER_LOW = 25.0
    MAX_MIGRATION = 40.0
    MIN_KNOWLEDGE_CONFIDENCE = 0.20

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
        if action.amount < 0 or action.source_node not in world.nodes:
            return False

        if action.action_type == "migrate":
            if action.target_node is None or action.source_node == action.target_node:
                return False
            if action.target_node not in world.nodes:
                return False
            if not 0 < action.amount <= self.MAX_MIGRATION:
                return False
            if action.knowledge_confidence < self.MIN_KNOWLEDGE_CONFIDENCE:
                return False

            source = world.nodes[action.source_node]
            target = world.nodes[action.target_node]

            # Execution-time revalidation closes the stale-state race between
            # planning and acting. Distributed knowledge may be old, but a
            # physically unsafe target is never accepted.
            if not source.network_ok or not target.network_ok:
                return False
            if target.temperature_c >= self.THERMAL_DEGRADED or target.power_pct <= self.POWER_LOW:
                return False
            if target.free_cpu < action.amount:
                return False
            return True

        if action.action_type == "isolate":
            node = world.nodes[action.source_node]
            return node.critical_workload <= 0 or node.status in {NodeStatus.CRITICAL, NodeStatus.DEGRADED}

        if action.action_type == "shed":
            node = world.nodes[action.source_node]
            return action.amount <= max(0.0, node.workload - node.critical_workload)

        return action.action_type in {"reduce_power"}
