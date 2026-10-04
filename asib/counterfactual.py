from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .action_executor import ActionExecutor
from .mission import MissionEvaluator
from .policy import SafetyPolicy
from .resources import migration_power_floor
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
        mission: MissionEvaluator | None = None,
    ):
        self.executor = executor or ActionExecutor()
        self.validator = validator or SafetyValidator()
        self.policy = SafetyPolicy()
        self.mission = mission or MissionEvaluator()

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
            previous_temperature = {
                node_id: node.temperature_c for node_id, node in shadow.nodes.items()
            }
            previous_power = {
                node_id: node.power_pct for node_id, node in shadow.nodes.items()
            }
            for _ in range(horizon_ticks):
                future_sim.advance_physics()

                operationally_safe = self.validator.validate(shadow).safe
                touched_nodes = {
                    node_id
                    for action in actions
                    for node_id in (action.source_node, action.target_node)
                    if node_id is not None
                }
                mitigating_sources = {
                    action.source_node
                    for action in actions
                    if action.action_type in {"migrate", "shed", "reduce_power"}
                }
                migration_targets = {
                    action.target_node
                    for action in actions
                    if action.action_type == "migrate" and action.target_node is not None
                }
                if operationally_safe:
                    for node_id in touched_nodes:
                        node = shadow.nodes[node_id]
                        if node.temperature_c >= self.policy.THERMAL_CRITICAL:
                            if (
                                node.temperature_c >= self.validator.THERMAL_HARD_LIMIT
                                or node_id not in mitigating_sources
                                or previous_temperature.get(node_id, node.temperature_c) < node.temperature_c
                            ):
                                operationally_safe = False
                                break
                        if node.power_pct <= self.policy.POWER_CRITICAL:
                            if (
                                node.power_pct <= self.validator.POWER_HARD_FLOOR
                                or node_id not in mitigating_sources
                                or previous_power.get(node_id, node.power_pct) > node.power_pct
                            ):
                                operationally_safe = False
                                break

                if operationally_safe:
                    for node_id in migration_targets:
                        node = shadow.nodes[node_id]
                        if (
                            node.network_ok
                            and node.power_pct <= migration_power_floor(shadow)
                            and node.workload > node.critical_workload
                        ):
                            operationally_safe = False
                            break

                if not operationally_safe:
                    future_safe = False
                    future_failure_tick = shadow.tick
                    break

                previous_temperature = {
                    node_id: node.temperature_c for node_id, node in shadow.nodes.items()
                }
                previous_power = {
                    node_id: node.power_pct for node_id, node in shadow.nodes.items()
                }

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
