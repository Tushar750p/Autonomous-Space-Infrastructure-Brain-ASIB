from .mission import MissionEvaluator
from .runtime import ASIBRuntime
from .simulator import Simulator


def run_compound_benchmark(ticks: int = 20) -> dict:
    sim = Simulator()
    sim.inject_thermal_failure("orbital-node-01", 98)
    sim.inject_power_failure("orbital-node-02", 18)
    sim.inject_network_failure("orbital-node-03")
    sim.world.nodes["orbital-node-03"].critical_workload = 0
    sim.inject_comms_delay(5.0)

    runtime = ASIBRuntime(sim)
    reports = runtime.run(ticks)

    scores = [MissionEvaluator().evaluate(sim.world)]
    final = scores[-1]
    return {
        "ticks": ticks,
        "final_mission": final,
        "memory_entries": len(sim.world.memory),
        "robot_states": {k: v.__dict__ for k, v in runtime.robots.robots.items()},
        "reports": reports,
    }
