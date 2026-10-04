from .engine import ASIBBrain
from .simulator import Simulator


def main():
    sim = Simulator()
    brain = ASIBBrain()

    print("ASIB V1.0 — Autonomous Space Infrastructure Brain")
    print("Earth-based digital-twin testbed\n")

    print("Initial state")
    for node_id, state in sim.snapshot().items():
        print(f"  {node_id}: temp={state['temperature_c']}C power={state['power_pct']}% load={state['workload']}")

    print("\nScenario: thermal + power stress on orbital-node-01")
    sim.inject_thermal_failure("orbital-node-01")
    sim.inject_power_failure("orbital-node-01", 18)

    events = brain.step(sim.world)
    for event in events:
        print(f"[{event.severity}] {event.event_type:<14} {event.node_id}: {event.message}"
              + (f" | action={event.action}" if event.action else ""))

    print("\nPost-decision state")
    for node_id, state in sim.snapshot().items():
        print(f"  {node_id}: temp={state['temperature_c']}C power={state['power_pct']}% load={state['workload']} status={state['status']}")

    print(f"\nAutonomy mode: {sim.world.autonomy_mode.value}")
    print(f"Memory entries: {len(sim.world.memory)}")


if __name__ == "__main__":
    main()
