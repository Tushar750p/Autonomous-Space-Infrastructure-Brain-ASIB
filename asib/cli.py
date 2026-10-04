from .engine import ASIBBrain
from .simulator import Simulator

def main():
    sim = Simulator()
    brain = ASIBBrain()
    print("ASIB V0.1 — Autonomous Space Infrastructure Brain")
    print("Earth-based orbital infrastructure simulation\n")
    print("Initial state:")
    for k, v in sim.snapshot().items():
        print(k, v)

    print("\nInjecting thermal failure into orbital-node-01...")
    sim.inject_thermal_failure("orbital-node-01")
    events = brain.step(sim.world)
    for event in events:
        print(f"[{event.event_type}] {event.node_id}: {event.message} | action={event.action}")

    print("\nFinal state:")
    for k, v in sim.snapshot().items():
        print(k, v)

if __name__ == "__main__":
    main()
