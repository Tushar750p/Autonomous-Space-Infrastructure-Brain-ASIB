from .models import Event, NodeStatus, World

class ASIBBrain:
    """Deterministic safety-first controller for the V1 simulator."""

    def observe(self, world: World) -> list[Event]:
        events = []
        for node in world.nodes.values():
            if node.temperature_c >= 85:
                node.status = NodeStatus.CRITICAL
                events.append(Event("thermal", node.node_id, "Critical temperature detected"))
            elif node.temperature_c >= 70 or node.power_pct < 25 or not node.network_ok:
                node.status = NodeStatus.DEGRADED
                events.append(Event("degradation", node.node_id, "Infrastructure degradation detected"))
            else:
                node.status = NodeStatus.NOMINAL
        return events

    def decide(self, world: World, events: list[Event]) -> list[Event]:
        actions = []
        for event in events:
            node = world.nodes[event.node_id]
            if event.event_type == "thermal":
                node.workload = max(10.0, node.workload - 30.0)
                node.cpu_load = max(0.10, node.cpu_load - 0.25)
                event.action = "shed_noncritical_workload"
                actions.append(event)
            elif event.event_type == "degradation" and not node.network_ok:
                node.workload = max(10.0, node.workload - 20.0)
                event.action = "isolate_network_degraded_node"
                actions.append(event)
            elif event.event_type == "degradation" and node.power_pct < 25:
                node.workload = max(10.0, node.workload - 25.0)
                event.action = "reduce_power_load"
                actions.append(event)
            elif event.event_type == "degradation":
                node.workload = max(10.0, node.workload - 15.0)
                event.action = "reduce_compute_load"
                actions.append(event)
        return actions

    def verify(self, world: World, actions: list[Event]) -> list[Event]:
        results = []
        for action in actions:
            node = world.nodes[action.node_id]
            # Simple deterministic thermal response for the V1 world model.
            if action.action in {"shed_noncritical_workload", "reduce_compute_load", "reduce_power_load"}:
                node.temperature_c = max(25.0, node.temperature_c - 8.0)
                node.cpu_load = min(node.cpu_load, 0.65)
            node.status = NodeStatus.NOMINAL if node.temperature_c < 70 and node.power_pct >= 25 and node.network_ok else NodeStatus.DEGRADED
            results.append(Event("verification", node.node_id, f"Recovery result: {node.status.value}", action.action))
        return results

    def step(self, world: World) -> list[Event]:
        world.tick += 1
        detected = self.observe(world)
        actions = self.decide(world, detected)
        verified = self.verify(world, actions)
        history = detected + verified
        world.memory.extend(history)
        return history
