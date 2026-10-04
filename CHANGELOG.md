# Changelog

## 0.5.2 — 2026-10-04

### Added
- Deterministic Monte Carlo-style robustness execution and CLI.
- Configurable mission-priority scoring profiles.
- Scalable deterministic multi-node simulation.
- Optional SQLite operational event and decision persistence.
- Robustness and scalability test coverage.

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
