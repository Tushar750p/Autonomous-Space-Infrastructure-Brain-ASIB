# 🛰️ Autonomous Space Infrastructure Brain — ASIB

**ASIB** is an Earth-based research testbed for a future autonomous operating layer for distributed off-Earth infrastructure.

> **Research/simulation only:** this repository is not flight software and is not intended to command real spacecraft or physical hardware.

> **Mission:** coordinate compute, power, thermal headroom, communications and recovery across many autonomous infrastructure nodes while Earth contact is delayed or unavailable.


## Core loop

```
Telemetry
   ↓
Digital Twin / World State
   ↓
Observer-specific Knowledge
   ↓
Observe & Detect
   ↓
Safety Policy
   ↓
Uncertainty-aware Multi-Node Planner
   ↓
Execute
   ↓
Verify
   ↓
Infrastructure Memory
   ↺
```

## What is implemented

- 🛰️ Scalable deterministic virtual orbital compute nodes (3 by default)
- 💻 Compute/workload modelling
- 🌡️ Thermal modelling
- ⚡ Power reserve modelling
- 📡 Network topology + simulated communication delay
- ☀️ Deterministic orbital sunlight/eclipse power environment
- 🧮 Plan-local resource reservations and eclipse-aware power floors
- 🌍 Simulated intermittent Earth contact
- 💥 Thermal, power, network-partition and compute fault injection
- 🔄 Multi-node workload migration
- 🧠 Infrastructure event memory and querying
- 🔮 Transparent risk prediction with trend, confidence and horizon
- 🧩 Observer-specific distributed knowledge with stale-state modelling
- 🎯 Uncertainty-aware target selection for workload migration
- 🛡️ Safety guardrails for autonomous actions
- ✅ Execution-aware verification
- ✅ Explicit post-action safety invariants
- ✅ Tamper-evident decision ledger (SHA-256 chain)
- ✅ Simulation-only hardware-in-the-loop boundary
- ✅ Pre-execution counterfactual simulation over a future physics horizon
- ✅ Reproducible passive-vs-ASIB experiment suite
- ✅ Deterministic state replay including orbital environment
- ✅ Forecast outcome calibration with Brier-score tracking
- ✅ Deterministic Monte Carlo-style robustness suite
- ✅ Complete JSON-safe world checkpoints with restore support
- ✅ Configurable mission-priority profiles
- ✅ Constraint-based counterfactual plan optimization
- ✅ Optional SQLite persistence for operational events and decisions
- ✅ Tamper-evident decision ledger with verifiable hash chain
- 🎯 Mission-health evaluation
- 🖥️ Browser control room with continuous autonomous ticks
- 🤖 Simulated maintenance-robot fleet with failure/reassignment recovery
- 🧾 Decision traces for every autonomous planning cycle
- 📊 Reproducible compound benchmark with recovery, score-delta and unsafe-event metrics
- 🧪 Unit + system tests + GitHub Actions CI
- 🩺 Service health, metrics, audit, replay, calibration and incident-postmortem API endpoints
- 🐳 Docker + Docker Compose support

## Run locally

```bash
python -m asib.cli
python run_asib.py compound
python run_benchmark.py --ticks 20
python run_experiments.py --ticks 20
python -m asib.selftest 5
python -m asib.scenario_cli eclipse
python -m asib.robustness_cli --ticks 5 --trials 5
python -m asib.lab_cli --ticks 3 --robustness-trials 2
asib-checkpoint --scenario compound --ticks 3 --path asib-checkpoint.json
python -m unittest discover -s tests -v
```

### Company-facing demo

The repository includes a self-contained interactive demo for company, partner and investor review.

**Browser demo (GitHub Pages):**  
`https://tushar750p.github.io/Autonomous-Space-Infrastructure-Brain-ASIB/`

**Live autonomous backend / control room (Railway):**  
`https://asib-mission-control-production.up.railway.app`

The browser demo is intentionally simulation-only. The Railway service runs the Python autonomous runtime and exposes the operational API/control room. It visualizes infrastructure topology, mission health, risk forecasts, autonomous decisions and fault-recovery scenarios without connecting to real spacecraft or physical actuators.

## Control room

```bash
python -c "from asib.dashboard import run; run(host='0.0.0.0', port=8080)"
```

Open `http://localhost:8080`.

The package also supports `python -m asib` as a direct CLI entry point, `asib-scenario <name>` for deterministic research scenarios, `asib-checkpoint` for checkpoint artifacts, and `asib-lab` for the complete local validation suite.

### Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`.

Health endpoint: `http://localhost:8080/api/health`

Metrics endpoint: `http://localhost:8080/api/metrics`

Audit export: `http://localhost:8080/api/audit`

Replay export: `http://localhost:8080/api/replay`

Incident postmortem: `http://localhost:8080/api/postmortem`

Robustness validation: `http://localhost:8080/api/robustness?ticks=5&trials=5`

Storage status: `http://localhost:8080/api/storage`

Forecast calibration export: `http://localhost:8080/api/calibration`

Environment variables: `ASIB_HOST`, `ASIB_PORT`, `ASIB_TICK_INTERVAL_S`, `ASIB_STORE_PATH`.

Set `ASIB_STORE_PATH=/data/asib.db` to persist operational events and decision traces in SQLite.

For larger simulations, instantiate `Simulator(node_count=N)`; the default remains 3 nodes.

## Example autonomous scenario

Inject a thermal fault into `orbital-node-01`.

ASIB can:
1. detect the unsafe thermal condition
2. evaluate reclaimable workload
3. consult an observer-specific, potentially delayed view of candidate nodes
4. avoid targets whose state confidence is too low
5. select a healthy connected node using an uncertainty penalty
6. migrate workload within a policy limit
7. preserve critical workload
8. verify the resulting state
9. store the decision trace

## Architecture

```
asib/
├── models.py          # world, nodes, actions, events
├── simulator.py       # deterministic digital twin + fault injection
├── environment.py     # orbital sunlight/eclipse environment
├── resources.py       # resource envelopes + plan-local reservations
├── policy.py          # safety boundaries
├── planner.py         # uncertainty-aware multi-node recovery planning
├── optimizer.py       # bounded counterfactual plan optimization
├── engine.py          # observe / shadow / execute / verify loop
├── action_executor.py # centralized safe actuation
├── counterfactual.py  # future-horizon shadow validation
├── distributed.py     # delayed observer-specific infrastructure knowledge
├── memory.py          # operational memory
├── predictor.py       # transparent trend-aware risk scoring
├── mission.py         # mission health metrics
├── comms.py           # delayed communication model
├── network.py         # node topology and partitions
├── telemetry.py       # telemetry history
├── calibration.py     # forecast outcome calibration
├── robotics.py        # safe maintenance-robot simulator
├── hil.py             # simulation-only hardware boundary
├── audit.py           # tamper-evident decision ledger
├── replay.py          # tamper-evident deterministic state replay
├── health.py          # consolidated operational health
├── postmortem.py      # incident postmortem generator
├── checkpoint.py      # complete world checkpoint export/restore
├── checkpoint_cli.py  # checkpoint artifact command-line interface
├── robustness.py      # deterministic robustness trials
├── robustness_cli.py  # robustness command-line interface
├── storage.py         # optional SQLite operational persistence
├── lab.py             # combined research validation orchestration
├── lab_cli.py         # combined research validation CLI
├── runtime.py         # closed-loop autonomous runtime
├── benchmark.py       # reproducible system benchmark
├── scenarios.py       # repeatable fault scenarios
├── scenario_cli.py    # scenario command-line interface
├── robustness_cli.py  # robustness command-line interface
└── dashboard.py       # autonomous browser control room
```

## Research direction

The long-term research problem is **cross-infrastructure autonomy**:

> How can heterogeneous off-Earth systems cooperatively manage limited power, thermal headroom, compute, communications and maintenance resources under partial observability?

ASIB V2 adds a concrete partial-observability mechanism: each infrastructure node has an observer-specific knowledge view. State updates travel through simulated links with delay, stale knowledge lowers confidence, and the planner penalizes uncertainty instead of blindly trusting old state.

The simulator also includes an orbital sunlight/eclipse cycle. Solar input and thermal bias change with orbital phase, so recovery policies can be tested against a changing space-specific environment rather than static faults alone.

See [RESEARCH.md](RESEARCH.md) for current positioning and prior-art notes.

## Roadmap

**V1 — Earth digital twin:** multi-node autonomy, faults, policies, memory and telemetry ✅

**V1.5 — Physics + Prediction:** richer thermal/power dynamics, telemetry trends, topology and maintenance-robot simulation ✅

**V2 — Distributed autonomy:** delayed observer-specific knowledge, communication-aware planning, uncertainty-aware coordination, execution-time revalidation and explicit safety invariants ✅

**V3 — Safe test interfaces:** simulation-only hardware-in-the-loop boundary and tamper-evident decision audit ✅

**V4 — Validation harness:** reproducible passive-vs-ASIB experiments across nine scenarios, future-horizon counterfactual validation and forecast calibration ✅

**V5 — Environmental autonomy:** deterministic orbital eclipse/sunlight dynamics, plan-local resource reservations, environment-aware energy margins and maintenance failure recovery ✅

**V5.5 — Research validation:** deterministic robustness trials, configurable mission profiles, forecast calibration and persistent operational journaling ✅

**V6 — Space integration study:** mission-specific integration research, future hardware qualification and independent verification

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Intellectual property

This repository is experimental software, not a patent opinion. Before patent-sensitive disclosure, perform a dedicated prior-art/patent review and document novel claims independently.
