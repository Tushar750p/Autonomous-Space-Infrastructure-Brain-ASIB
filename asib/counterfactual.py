from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .action_executor import ActionExecutor
from .mission import MissionEvaluator
from .models import Action, World
from .simulator import Simulator
from .validation import InvariantViolation, SafetyValidator


@dataclass(frozen=True)
class ShadowReport:
    accepted: bool
    before_score: float
    after_score: float
    score_delta: float
    executed_actions: int
    violations: list[InvariantViolation]
    horizon_ticks: int = 0
    future_safe: bool = True
    future_failure_tick: int | None = None

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "before_score": self.before_score,
            "after_score": self.after_score,
            "score_delta": self.score_delta,
            "executed_actions": self.executed_actions,
            "violations": [violation.__dict__ for violation in self.violations],
            "horizon_ticks": self.horizon_ticks,
            "future_safe": self.future_safe,
            "future_failure_tick": self.future_failure_tick,
        }


class CounterfactualEvaluator:
    """Runs proposed plans in a cloned world and checks a future safety horizon."""

    def __init__(
        self,
        executor: ActionExecutor | None = None,
        validator: SafetyValidator | None = None,
    ):
        self.executor = executor or ActionExecutor()
        self.validator = validator or SafetyValidator()
        self.mission = MissionEvaluator()

    def evaluate(
        self,
        world: World,
        actions: list[Action],
        trace_id: str,
        horizon_ticks: int = 2,
    ) -> ShadowReport:
        shadow = deepcopy(world)
        before = self.mission.evaluate(shadow)["score"]
        events = self.executor.execute(shadow, actions, trace_id)
        after = self.mission.evaluate(shadow)["score"]

        executed = sum(1 for event in events if event.event_type == "action")
        violations = [
            event for event in events if event.event_type == "invariant_violation"
        ]

        future_safe = True
        future_failure_tick = None

        # Reuse the simulator's deterministic physics rather than duplicating
        # the dynamics inside the counterfactual engine.
        if not violations and horizon_ticks > 0:
            future_sim = Simulator()
            future_sim.world = shadow
            for _ in range(horizon_ticks):
                future_sim.advance_physics()
                if not self.validator.validate(shadow).safe:
                    future_safe = False
                    future_failure_tick = shadow.tick
                    break

        accepted = (
            executed == len(actions)
            and not violations
            and future_safe
        )

        future_violations = [] if future_safe else self.validator.validate(shadow).violations

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
            ] + list(future_violations),
            horizon_ticks=max(0, horizon_ticks),
            future_safe=future_safe,
            future_failure_tick=future_failure_tick,
        )
