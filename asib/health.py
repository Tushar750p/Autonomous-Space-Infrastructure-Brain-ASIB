from __future__ import annotations

from .mission import MissionEvaluator
from .resources import system_resource_report
from .validation import SafetyValidator


class HealthService:
    """Aggregates service health without exposing physical-control interfaces."""

    def __init__(self, runtime):
        self.runtime = runtime

    def snapshot(self) -> dict:
        world = self.runtime.world
        mission = MissionEvaluator().evaluate(world)
        invariants = SafetyValidator().validate(world)
        audit_valid = world.audit_ledger.verify()
        replay_valid = self.runtime.replay.validate()

        return {
            "status": "ok" if (
                invariants.safe and audit_valid and replay_valid
            ) else "degraded",
            "tick": world.tick,
            "mission_score": mission["score"],
            "autonomy_mode": world.autonomy_mode.value,
            "earth_contact_available": world.earth_contact_available,
            "environment": world.environment.snapshot(),
            "resources": system_resource_report(world),
            "safety_invariants": invariants.safe,
            "audit_chain": audit_valid,
            "replay_journal": replay_valid,
            "forecast_calibration": self.runtime.forecasts.summary(),
            "storage": self.runtime.storage_status(),
            "memory_entries": len(world.memory),
        }
