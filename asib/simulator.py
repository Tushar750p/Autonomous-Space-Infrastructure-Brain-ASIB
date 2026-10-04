from .models import Node, NodeStatus, World
from .network import NetworkModel


class Simulator:
    """Deterministic Earth-based digital twin for ASIB development."""

    def __init__(self):
        self.world = World(nodes={
            "orbital-node-01": Node(
                "orbital-node-01", cpu_load=45, temperature_c=50,
                power_pct=78, workload=70, critical_workload=25
            ),
            "orbital-node-02": Node(
                "orbital-node-02", cpu_load=35, temperature_c=48,
                power_pct=75, workload=55, critical_workload=15
            ),
            "orbital-node-03": Node(
                "orbital-node-03", cpu_load=20, temperature_c=42,
                power_pct=88, workload=35, critical_workload=10
            ),
        })
        NetworkModel().ensure_full_mesh(self.world)

    def inject_thermal_failure(self, node_id: str, temperature_c: float = 92.0):
        self.world.nodes[node_id].temperature_c = temperature_c

    def inject_power_failure(self, node_id: str, power_pct: float = 18.0):
        self.world.nodes[node_id].power_pct = power_pct

    def inject_network_failure(self, node_id: str):
        self.world.nodes[node_id].network_ok = False

    def inject_network_partition(self, node_id: str):
        NetworkModel().partition_node(self.world, node_id)

    def inject_compute_overload(self, node_id: str, extra_load: float = 45.0):
        node = self.world.nodes[node_id]
        node.cpu_load = min(100.0, node.cpu_load + extra_load)
        node.workload += extra_load

    def inject_comms_delay(self, delay_s: float):
        self.world.comms_delay_s = max(0.0, delay_s)

    def inject_earth_contact_loss(self):
        self.world.earth_contact_available = False

    def restore_earth_contact(self):
        self.world.earth_contact_available = True

    def advance_physics(self):
        self.world.environment.advance()

        for node in self.world.nodes.values():
            if node.status == NodeStatus.ISOLATED:
                continue

            utilization = node.cpu_load / max(node.cpu_capacity, 1.0)
            node.temperature_c = max(
                20.0,
                min(
                    110.0,
                    node.temperature_c
                    + max(-3.0, utilization * 5.0 - 1.5)
                    + self.world.environment.cooling_bias_c,
                ),
            )
            drain = max(0.2, utilization * 2.5)
            node.power_pct = max(
                0.0,
                min(
                    100.0,
                    node.power_pct
                    + self.world.environment.solar_generation_pct
                    - drain,
                ),
            )
            node.cpu_load = max(0.0, min(100.0, node.workload))

            if not node.network_ok:
                node.status = NodeStatus.DEGRADED

        self.world.tick += 1

    def snapshot(self):
        return {
            "_environment": self.world.environment.snapshot(),
            node_id: {
                "cpu_load": round(node.cpu_load, 2),
                "temperature_c": round(node.temperature_c, 2),
                "power_pct": round(node.power_pct, 2),
                "storage_pct": round(node.storage_pct, 2),
                "network_ok": node.network_ok,
                "latency_ms": round(node.latency_ms, 2),
                "workload": round(node.workload, 2),
                "critical_workload": round(node.critical_workload, 2),
                "status": node.status.value,
            }
            for node_id, node in self.world.nodes.items()
        }
