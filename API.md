# ASIB Operational API

The local control room exposes JSON endpoints for simulation inspection. These endpoints do not provide physical command interfaces.

| Endpoint | Purpose |
| --- | --- |
| `/api/state` | Full current simulation state, risks, mission metrics, resources, audit, replay and latest decision intelligence |
| `/api/decision` | Latest and recent autonomous decision traces with explainable confidence, evidence and risk level |
| `/api/tick` | Advance one deterministic simulation tick |
| `/api/reset` | Reset the testbed to its initial deterministic state |
| `/api/health` | Consolidated safety, audit, replay and service-health snapshot |
| `/api/metrics` | Compact operational metrics payload |
| `/api/audit` | Export the tamper-evident decision ledger |
| `/api/replay` | Export the tamper-evident deterministic replay journal |
| `/api/calibration` | Export pending/completed forecast calibration records |
| `/api/postmortem` | Generate the latest incident postmortem summary |
| `/api/storage` | Show optional SQLite persistence status and record counts |
| `/api/checkpoint` | Export a JSON-safe complete simulation world checkpoint |
| `/api/robustness?ticks=<n>&trials=<n>` | Run deterministic Monte Carlo-style robustness trials |
| `/api/scenario?name=<name>` | Inject a research scenario and advance one tick |
| `/api/experiments?ticks=<n>` | Run the reproducible passive-vs-ASIB validation suite |

Scenario names include `thermal`, `power`, `compute`, `network`, `partition`, `earth-loss`, `eclipse`, `robot-failure`, and `compound`.
