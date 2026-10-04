from .engine import ASIBBrain
from .runtime import ASIBRuntime
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
    elif name == "partition":
        sim.inject_network_partition("orbital-node-02")
    elif name == "compute":
        sim.inject_compute_overload("orbital-node-01", 45)
    elif name == "earth-loss":
        sim.inject_earth_contact_loss()
    elif name == "compound":
        sim.inject_thermal_failure("orbital-node-01", 96)
        sim.inject_power_failure("orbital-node-02", 20)
        sim.inject_network_failure("orbital-node-03")
        sim.world.nodes["orbital-node-03"].critical_workload = 0
        sim.inject_network_partition("orbital-node-02")
        sim.inject_comms_delay(12.0)
        sim.inject_earth_contact_loss()
    else:
        raise ValueError(f"Unknown scenario: {name}")

    # Runtime scenarios exercise the same closed loop used by the control room.
    runtime = ASIBRuntime(sim)
    report = runtime.tick()

    return {
        "scenario": name,
        "mode": sim.world.autonomy_mode.value,
        "events": report.events,
        "risks": report.risks,
        "state": report.state,
        "knowledge": report.knowledge,
        "memory_entries": report.memory_entries,
    }
