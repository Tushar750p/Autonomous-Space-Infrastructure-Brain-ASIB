from __future__ import annotations

from dataclasses import dataclass

from .mission import MissionEvaluator
from .predictor import RiskPredictor


@dataclass(frozen=True)
class IncidentPostmortem:
    tick: int
    severity: str
    affected_nodes: list[str]
    root_causes: list[str]
    actions_taken: list[str]
    verification: list[str]
    unresolved_risks: list[str]
    mission: dict
    decision_class: str
    audit_valid: bool

    def as_dict(self) -> dict:
        return self.__dict__


class PostmortemService:
    """Converts the latest autonomous trace into a concise operational incident record."""

    def __init__(self, runtime):
        self.runtime = runtime

    def generate(self) -> IncidentPostmortem:
        world = self.runtime.world
        recent = world.memory[-80:]
        critical = [e for e in recent if e.severity == "critical"]
        warnings = [e for e in recent if e.severity == "warning"]
        actions = [e for e in recent if e.event_type in {"action", "adapter_apply"}]
        verification = [e for e in recent if e.event_type == "verification"]

        causes: list[str] = []
        for event in recent:
            if event.event_type in {"critical", "degradation", "earth_contact", "robot_failure"}:
                if event.message not in causes:
                    causes.append(event.message)

        risks = RiskPredictor().predict(world)
        unresolved = [
            f"{risk.node_id}: score={risk.score}, interval=[{risk.score_low}, {risk.score_high}]"
            for risk in risks
            if risk.score >= 40
        ]

        decision = world.decision_log[-1] if world.decision_log else {}
        severity = "critical" if critical else "warning" if warnings else "info"

        return IncidentPostmortem(
            tick=world.tick,
            severity=severity,
            affected_nodes=sorted({e.node_id for e in critical + warnings if e.node_id != "earth"}),
            root_causes=causes[-10:],
            actions_taken=[e.message for e in actions[-10:]],
            verification=[e.message for e in verification[-10:]],
            unresolved_risks=unresolved[:10],
            mission=self.runtime.mission.evaluate(world),
            decision_class=decision.get("decision_class", "hold"),
            audit_valid=world.audit_ledger.verify(),
        )
