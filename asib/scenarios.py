from .runtime import ASIBRuntime
from .simulator import Simulator


def run_fault_scenario(name: str) -> dict:
    sim = Simulator()
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
    elif name == "eclipse":
        sim.world.environment.phase_deg = 120.0
        sim.world.nodes["orbital-node-02"].power_pct = 40.0
    elif name == "eclipse-compound":
        sim.world.environment.phase_deg = 120.0
        sim.inject_thermal_failure("orbital-node-01", 96)
        sim.inject_power_failure("orbital-node-02", 40)
        sim.world.nodes["orbital-node-03"].critical_workload = 0
        sim.inject_network_failure("orbital-node-03")
        sim.inject_network_partition("orbital-node-02")
        sim.inject_comms_delay(12.0)
        sim.inject_earth_contact_loss()
    elif name == "robot-failure":
        runtime = ASIBRuntime(sim)
        runtime.robots.enqueue("orbital-node-01", "inspect-and-service", priority=100)
        runtime.robots.dispatch()
        runtime.robots.step()
        failure_event = runtime.robots.inject_failure("maintenance-01")
        report = runtime.tick()
        report.events.insert(0, failure_event.__dict__)
        sim.world.memory.append(failure_event)
        return {
            "scenario": name,
            "mode": sim.world.autonomy_mode.value,
            "events": report.events,
            "risks": report.risks,
            "state": report.state,
            "knowledge": report.knowledge,
            "memory_entries": report.memory_entries,
            "environment": report.environment,
            "resources": report.resources,
            "forecast_calibration": report.forecast_calibration,
        }
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
        "environment": report.environment,
        "resources": report.resources,
        "forecast_calibration": report.forecast_calibration,
    }
