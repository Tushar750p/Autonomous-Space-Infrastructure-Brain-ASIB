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
        mission = self.runtime.mission.evaluate(world)
        invariants = SafetyValidator().validate(world)
        audit_valid = world.audit_ledger.verify()
        replay_valid = self.runtime.replay.validate()
        last_decision = world.decision_log[-1] if world.decision_log else None
        needs_human_review = bool(last_decision and last_decision.get("needs_human_review"))

        return {
            "status": "degraded" if (
                needs_human_review or not invariants.safe or not audit_valid or not replay_valid
            ) else "ok",
            "tick": world.tick,
            "mission_score": mission["score"],
            "autonomy_mode": world.autonomy_mode.value,
            "decision_class": last_decision.get("decision_class") if last_decision else None,
            "needs_human_review": needs_human_review,
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
