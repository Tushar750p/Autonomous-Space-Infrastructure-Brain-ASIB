# Changelog

## 0.6.0 — 2026-10-06

### Decision intelligence
- Added an explainable decision-assessment layer for every autonomous cycle.
- Decision traces now include bounded confidence, risk level, knowledge-state confidence, shadow score delta, future-safety evidence and invariant evidence.
- Added `/api/decision` for latest/recent decision traces.
- Control room now surfaces decision confidence and risk level alongside mission health.
- Added regression coverage for safe decisions and human-review escalation.

## 0.5.3 — 2026-10-05

### Recovery and autonomy
- Restored isolated-node status automatically when simulated network coordination returns.
- Added explicit network-recovery event telemetry.
- Added regression coverage for isolation, recovery and repeated-isolation prevention.
- Expanded bounded emergency optimizer search and aligned validation coverage.

### Validation
- GitHub Actions CI passes across Python 3.10, 3.11 and 3.12.
- Railway deployment configuration remains the production deployment path.
- Dashboard health now surfaces human-review escalation state.
- Dashboard experiment and robustness parameters are validated and invalid requests return HTTP 400.
- Production SQLite storage is backed by a persistent Railway volume mounted at `/data`.
- Dashboard refreshes now avoid overlapping requests and defer expensive checkpoint/postmortem/storage refreshes.
- HTTP access logs are routed through ASIB logging to avoid false error-level request entries.

## 0.5.2 — 2026-10-04

### Added
- Deterministic Monte Carlo-style robustness execution and CLI.
- Configurable mission-priority scoring profiles.
- Scalable deterministic multi-node simulation.
- Optional SQLite operational event and decision persistence.
- Robustness and scalability test coverage.
- Constraint-based counterfactual plan optimization with bounded action search.
- Complete JSON-safe simulation checkpoints with restore support.
- Storage-aware prediction, resource envelopes and maintenance cleanup.
- Configurable mission profiles propagated through brain, counterfactual validation and runtime surfaces.

### Operations
- Docker Compose now persists the operational journal in a named volume.
- Control room exposes robustness and storage status endpoints.


## 0.5.1 — 2026-10-04

### Added
- Deterministic scenario CLI with eclipse and compound-environment scenarios.
- Direct `python -m asib` module entry point.
- Extended scenario runner outputs and test coverage.


## 0.5.0 — 2026-10-04

### Added
- Environment-driven dashboard service configuration.
- Container health checks and operational API endpoints.
- Operational metrics, audit and replay export endpoints.
- Autonomous incident postmortem generation.
- Forecast outcome calibration with Brier-score tracking.
- Migration-free emergency fallback planning after counterfactual rejection.
- Expanded orbital eclipse validation scenarios.
- Tamper-evident replay hash chain.
- Complete runtime report resource and forecast-calibration surfaces.

### Safety and validation
- Counterfactual validation checks future operational margins for migration targets.
- Integrated self-test covers forecast ledger health.
- Brain tests cover safe-plan repair and human-review escalation.
- Replay tests cover state-tampering detection.

### Packaging
- Published package metadata, Apache 2.0 licensing, classifiers and explicit package discovery.
- Docker/Compose runtime defaults are configurable through ASIB_HOST, ASIB_PORT and ASIB_TICK_INTERVAL_S.

ASIB remains an Earth-based research and simulation testbed; V6 mission-specific integration work is future research.
