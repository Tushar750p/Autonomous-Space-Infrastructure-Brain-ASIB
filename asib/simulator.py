from .models import Node, World

class Simulator:
    def __init__(self):
        self.world = World(nodes={
            "orbital-node-01": Node("orbital-node-01"),
            "orbital-node-02": Node("orbital-node-02", cpu_load=0.45, temperature_c=52, power_pct=72),
            "orbital-node-03": Node("orbital-node-03", cpu_load=0.25, temperature_c=40, power_pct=90),
        })

    def inject_thermal_failure(self, node_id: str):
        self.world.nodes[node_id].temperature_c = 92.0

    def inject_power_failure(self, node_id: str):
        self.world.nodes[node_id].power_pct = 18.0

    def inject_network_failure(self, node_id: str):
        self.world.nodes[node_id].network_ok = False

    def snapshot(self):
        return {node_id: vars(node).copy() for node_id, node in self.world.nodes.items()}
