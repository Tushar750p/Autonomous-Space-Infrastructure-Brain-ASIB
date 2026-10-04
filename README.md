# Autonomous Space Infrastructure Brain (ASIB)

ASIB is an Earth-based research testbed for a future autonomous operating layer for distributed off-Earth infrastructure.

**Research focus:** multi-node coordination under power, thermal, compute, network and communication constraints.

This project deliberately begins as a simulator. It does **not** issue commands to spacecraft, satellites, launch vehicles or other real-world systems.

## V1 architecture

```
Telemetry
   ↓
World State / Digital Twin
   ↓
Event Detection
   ↓
Constraint & Safety Policy
   ↓
Multi-node Planner
   ↓
Action Executor
   ↓
Verification
   ↓
Infrastructure Memory
```

### What V1 can demonstrate

- Multiple virtual orbital compute nodes
- Compute, power, thermal, storage and network state
- Communication delay / degraded connectivity
- Fault injection
- Workload migration between nodes
- Non-critical workload shedding
- Power conservation
- Network isolation
- Safety guardrails
- Post-action verification
- Event/decision memory
- Deterministic tests

## Run

```bash
python -m asib.cli
python -m unittest discover -s tests -v
```

The prototype uses only the Python standard library.

## Roadmap

1. V1: deterministic digital-twin simulator + autonomous recovery
2. V1.5: workload scheduler, richer thermal/power dynamics, fault scenarios
3. V2: communication topology, orbital motion abstractions and multi-agent coordination
4. V3: hardware-in-the-loop testbed
5. V4: research-grade verification, safety cases and flight-software integration study

## Current research boundary

ASIB is an experimental software architecture. It is not flight-qualified and should not control real spacecraft without extensive independent validation, formal safety analysis, hardware-in-the-loop testing and appropriate mission authorization.
