from __future__ import annotations

import argparse

from .checkpoint import save
from .runtime import ASIBRuntime
from .scenarios import run_fault_scenario
from .simulator import Simulator


def main() -> int:
    parser = argparse.ArgumentParser(description="Save an ASIB simulation checkpoint")
    parser.add_argument("--path", required=True, help="Output JSON checkpoint path")
    parser.add_argument("--ticks", type=int, default=0)
    parser.add_argument(
        "--scenario",
        choices=(
            "thermal", "power", "compute", "network", "partition",
            "earth-loss", "eclipse", "eclipse-compound", "robot-failure", "compound",
        ),
    )
    args = parser.parse_args()

    if args.scenario:
        result = run_fault_scenario(args.scenario)
        sim = Simulator()
        runtime = ASIBRuntime(sim)
        runtime.tick()
        # Scenario runner is intentionally side-effect free with respect to this
        # process; reproduce the scenario locally for a checkpoint artifact.
        if args.scenario == "thermal":
            sim.inject_thermal_failure("orbital-node-01")
        elif args.scenario == "power":
            sim.inject_power_failure("orbital-node-01", 12)
        elif args.scenario == "compute":
            sim.inject_compute_overload("orbital-node-01", 45)
        elif args.scenario == "network":
            sim.world.nodes["orbital-node-03"].critical_workload = 0
            sim.inject_network_failure("orbital-node-03")
        elif args.scenario == "partition":
            sim.inject_network_partition("orbital-node-02")
        elif args.scenario == "earth-loss":
            sim.inject_earth_contact_loss()
        elif args.scenario == "eclipse":
            sim.world.environment.phase_deg = 120.0
        elif args.scenario == "eclipse-compound":
            sim.world.environment.phase_deg = 120.0
            sim.inject_thermal_failure("orbital-node-01", 96)
            sim.inject_power_failure("orbital-node-02", 40)
            sim.world.nodes["orbital-node-03"].critical_workload = 0
            sim.inject_network_failure("orbital-node-03")
            sim.inject_network_partition("orbital-node-02")
            sim.inject_comms_delay(12.0)
            sim.inject_earth_contact_loss()
        elif args.scenario == "robot-failure":
            runtime.robots.enqueue("orbital-node-01", "inspect-and-service", priority=100)
            runtime.robots.dispatch()
            runtime.robots.step()
            runtime.robots.inject_failure("maintenance-01")
        elif args.scenario == "compound":
            sim.inject_thermal_failure("orbital-node-01", 96)
            sim.inject_power_failure("orbital-node-02", 20)
            sim.world.nodes["orbital-node-03"].critical_workload = 0
            sim.inject_network_failure("orbital-node-03")
            sim.inject_network_partition("orbital-node-02")
            sim.inject_comms_delay(12.0)
        runtime = ASIBRuntime(sim)
        runtime.run(max(0, args.ticks))
    else:
        runtime = ASIBRuntime()
        runtime.run(max(0, args.ticks))

    destination = save(runtime.world, args.path)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
