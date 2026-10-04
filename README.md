# Autonomous Space Infrastructure Brain (ASIB)

ASIB is an Earth-based research prototype for autonomous management of future off-Earth infrastructure.

## V1 goal

Simulate a small orbital infrastructure network and let an autonomous controller:
- observe compute, power, thermal and network state
- detect abnormal conditions
- choose safe recovery actions
- verify the result
- record the event as infrastructure memory

This repository is a **simulation/testbed**, not spacecraft flight software.

## Architecture

Telemetry -> State Model -> Decision Engine -> Action Executor -> Verification -> Memory

## Run

```bash
python -m asib.cli
```

The first prototype uses only the Python standard library.
