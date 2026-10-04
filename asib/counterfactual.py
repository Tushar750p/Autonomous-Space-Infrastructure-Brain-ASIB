from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .action_executor import ActionExecutor
from .mission import MissionEvaluator
from .models import Action, World
from .validation import InvariantViolation


@dataclass(frozen=True)
class ShadowReport:
    accepted: bool
    before_score: float
    after_score: float
    score_delta: float
    executed_actions: int
    violations: list[InvariantViolation]

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "before_score": self.before_score,
            "after_score": self.after_score,
            "score_delta": self.score_delta,
            "executed_actions": self.executed_actions,
            "violations": [violation.__dict__ for violation in self.violations],
        }


class CounterfactualEvaluator:
    """Runs a proposed plan in a cloned world before allowing live execution."""

    def __init__(self, executor: ActionExecutor | None = None):
        self.executor = executor or ActionExecutor()
        self.mission = MissionEvaluator()

    def evaluate(self, world: World, actions: list[Action], trace_id: str) -> ShadowReport:
        shadow = deepcopy(world)
        before = self.mission.evaluate(shadow)["score"]
        events = self.executor.execute(shadow, actions, trace_id)
        after = self.mission.evaluate(shadow)["score"]

        executed = sum(1 for event in events if event.event_type == "action")
        violations = [
            event for event in events if event.event_type == "invariant_violation"
        ]

        accepted = (
            executed == len(actions)
            and not violations
        )

        return ShadowReport(
            accepted=accepted,
            before_score=before,
            after_score=after,
            score_delta=round(after - before, 2),
            executed_actions=executed,
            violations=[
                InvariantViolation(
                    event.node_id,
                    event.action or "invariant_violation",
                    event.message,
                )
                for event in violations
            ],
        )
