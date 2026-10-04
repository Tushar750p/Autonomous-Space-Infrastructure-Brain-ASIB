# 🛰️ Autonomous Space Infrastructure Brain — ASIB

**ASIB** is an Earth-based research testbed for a future autonomous operating layer for distributed off-Earth infrastructure.

> **Mission:** coordinate compute, power, thermal headroom, communications and recovery across many autonomous infrastructure nodes while Earth contact is delayed or unavailable.

⚠️ **Research/simulation only.** ASIB does not control real spacecraft, launch vehicles, satellites or robots.

## Core loop

\`\`\`
Telemetry
   ↓
Digital Twin / World State
   ↓
Observe & Detect
   ↓
Safety Policy
   ↓
Multi-Node Planner
   ↓
Execute
   ↓
Verify
   ↓
Infrastructure Memory
   ↺
\`\`\`

## What is implemented

- 🛰️ Three virtual orbital compute nodes
- 💻 Compute/workload modelling
- 🌡️ Thermal modelling
- ⚡ Power reserve modelling
- 📡 Network topology + simulated communication delay
- 🌍 Simulated intermittent Earth contact
- 💥 Thermal, power, network-partition and compute fault injection
- 🔄 Multi-node workload migration
- 🧠 Infrastructure event memory and querying
- 🔮 Transparent risk prediction
- 🛡️ Safety guardrails for autonomous actions
- 🎯 Mission-health evaluation
- 🖥️ Browser control room with continuous autonomous ticks
- 🤖 Simulated maintenance-robot fleet
- 🔮 Trend-aware risk prediction with confidence/horizon
- 🧾 Decision traces for every autonomous planning cycle
- 📊 Reproducible compound benchmark
- 🧪 Unit + system tests + GitHub Actions CI
- 🐳 Docker + Docker Compose support

## Run locally

\`\`\`bash
python -m asib.cli
python run_asib.py compound
python run_benchmark.py --ticks 20
python -m unittest discover -s tests -v
\`\`\`

### Control room

\`\`\`bash
python -c "from asib.dashboard import run; run(host='0.0.0.0', port=8080)"
\`\`\`

Open \`http://localhost:8080\`.

### Docker

\`\`\`bash
docker compose up --build
\`\`\`

Open \`http://localhost:8080\`.

## Example autonomous scenario

Inject a thermal fault into \`orbital-node-01\`.

ASIB can:
1. detect the unsafe thermal condition
2. identify reclaimable workload
3. select a healthier node
4. migrate workload within a policy limit
5. preserve critical workload
6. verify the resulting state
7. store the decision trace

## Architecture

\`\`\`
asib/
├── models.py       # world, nodes, actions, events
├── simulator.py    # deterministic digital twin + fault injection
├── policy.py       # safety boundaries
├── planner.py      # multi-node recovery planning
├── engine.py       # observe / execute / verify loop
├── memory.py       # operational memory
├── predictor.py    # transparent risk scoring
├── mission.py      # mission health metrics
├── comms.py        # delayed communication model
├── network.py      # node topology and partitions
├── telemetry.py    # telemetry history
├── predictor.py    # trend-aware risk prediction
├── mission.py      # mission health metrics
├── memory.py       # operational memory
├── robotics.py     # safe maintenance-robot simulator
├── runtime.py      # closed-loop autonomous runtime
├── benchmark.py    # reproducible system benchmark
├── scenarios.py    # repeatable fault scenarios
└── dashboard.py    # autonomous browser control room
\`\`\`

## Research direction

The long-term research problem is **cross-infrastructure autonomy**:

> How can heterogeneous off-Earth systems cooperatively manage limited power, thermal headroom, compute, communications and maintenance resources under partial observability?

See [RESEARCH.md](RESEARCH.md) for current positioning and prior-art notes.

## Roadmap

**V1 — Earth digital twin:** multi-node autonomy, faults, policies, memory and telemetry ✅

**V1.5 — Physics + Prediction:** richer thermal/power dynamics, telemetry trends, topology and maintenance-robot simulation ✅

**V2 — Distributed autonomy:** communication partitions, asynchronous planning, uncertainty-aware coordination and benchmarked recovery

**V3 — Hardware-in-the-loop:** simulated interfaces for future physical testbeds, with strict separation from real mission control

**V4 — Research validation:** formal safety properties, reproducible benchmarks and independent verification

**V5 — Space integration study:** qualified interfaces and mission-specific integration research

## Intellectual property

This repository is experimental software, not a patent opinion. Before patent-sensitive disclosure, perform a dedicated prior-art/patent review and document novel claims independently.
