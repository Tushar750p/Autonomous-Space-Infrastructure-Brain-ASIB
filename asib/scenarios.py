from .engine import ASIBBrain
from .simulator import Simulator


def run_fault_scenario(name: str) -> dict:
    sim = Simulator()
    brain = ASIBBrain()

    if name == "thermal":
        sim.inject_thermal_failure("orbital-node-01")
    elif name == "power":
        sim.inject_power_failure("orbital-node-01", 12)
    elif name == "network":
        sim.world.nodes["orbital-node-03"].critical_workload = 0
        sim.inject_network_failure("orbital-node-03")
    elif name == "compound":
        sim.inject_thermal_failure("orbital-node-01", 96)
        sim.inject_power_failure("orbital-node-02", 20)
        sim.inject_network_failure("orbital-node-03")
        sim.world.nodes["orbital-node-03"].critical_workload = 0
        sim.inject_comms_delay(12.0)
    else:
        raise ValueError(f"Unknown scenario: {name}")

    events = brain.step(sim.world)
    return {
        "scenario": name,
        "mode": sim.world.autonomy_mode.value,
        "events": [event.__dict__ for event in events],
        "state": sim.snapshot(),
        "memory_entries": len(sim.world.memory),
    }
