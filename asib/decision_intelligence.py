from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Action


@dataclass(frozen=True)
class DecisionAssessment:
    """Explainable quality assessment for one autonomous planning cycle."""

    confidence: float
    risk_level: str
    action_count: int
    mean_knowledge_confidence: float
    shadow_score_delta: float
    future_safe: bool
    invariant_safe: bool
    evidence: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "confidence": round(self.confidence, 3),
            "confidence_pct": round(self.confidence * 100.0, 1),
            "risk_level": self.risk_level,
            "action_count": self.action_count,
            "mean_knowledge_confidence": round(self.mean_knowledge_confidence, 3),
            "shadow_score_delta": round(self.shadow_score_delta, 2),
            "future_safe": self.future_safe,
            "invariant_safe": self.invariant_safe,
            "evidence": list(self.evidence),
        }


class DecisionIntelligence:
    """Build a bounded, explainable confidence and risk assessment.

    This layer does not learn or mutate policy. It summarizes evidence already
    produced by the planner, counterfactual validator and executor so operators
    can see why a decision was trusted, repaired or escalated.
    """

    @staticmethod
    def assess(
        actions: Iterable[Action],
        shadow,
        invariant_safe: bool,
        decision_class: str,
        needs_human_review: bool,
    ) -> DecisionAssessment:
        actions = list(actions)
        confidences = [
            max(0.0, min(1.0, float(action.knowledge_confidence)))
            for action in actions
        ]
        mean_confidence = (
            sum(confidences) / len(confidences)
            if confidences
            else 1.0
        )

        confidence = 0.50
        evidence: list[str] = []

        if shadow.accepted:
            confidence += 0.20
            evidence.append("Counterfactual plan validation accepted")
        else:
            confidence -= 0.20
            evidence.append("Counterfactual validation rejected or unavailable")

        if shadow.future_safe:
            confidence += 0.15
            evidence.append(
                f"Future safety horizon={int(shadow.horizon_ticks)} tick(s) remained safe"
            )
        else:
            confidence -= 0.20
            evidence.append("Future safety horizon exposed a projected failure")

        if invariant_safe:
            confidence += 0.10
            evidence.append("Post-action safety invariants passed")
        else:
            confidence -= 0.20
            evidence.append("Post-action safety invariant violation detected")

        if actions:
            confidence += (mean_confidence - 0.50) * 0.10
            evidence.append(
                f"Mean action-state confidence={mean_confidence:.2f}"
            )
        else:
            confidence += 0.05
            evidence.append("No autonomous actuation required this cycle")

        if decision_class == "repair":
            confidence -= 0.05
            evidence.append("Primary plan was replaced by an emergency fallback")

        if needs_human_review:
            confidence -= 0.25
            evidence.append("Human review escalation is active")

        confidence = max(0.0, min(1.0, confidence))

        if needs_human_review or not shadow.future_safe or not invariant_safe:
            risk_level = "critical"
        elif decision_class == "repair" or confidence < 0.55:
            risk_level = "high"
        elif actions:
            risk_level = "medium"
        else:
            risk_level = "low"

        return DecisionAssessment(
            confidence=confidence,
            risk_level=risk_level,
            action_count=len(actions),
            mean_knowledge_confidence=mean_confidence,
            shadow_score_delta=float(shadow.score_delta),
            future_safe=bool(shadow.future_safe),
            invariant_safe=bool(invariant_safe),
            evidence=tuple(evidence),
        )
