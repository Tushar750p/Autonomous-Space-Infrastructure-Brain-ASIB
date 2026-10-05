from __future__ import annotations

from dataclasses import replace

from .counterfactual import CounterfactualEvaluator
from .models import Action, World
from .planner import Plan


class ConstrainedPlanOptimizer:
    """Searches a small deterministic neighborhood of plans before live execution."""

    # Explore both gentler and stronger bounded mitigation. Stronger variants
    # are essential during compound thermal/power emergencies, while the
    # executor still caps each action at the node's available non-critical load.
    RATIOS = (0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0)

    def __init__(self, counterfactual: CounterfactualEvaluator):
        self.counterfactual = counterfactual

    @staticmethod
    def _total_amount(actions: list[Action]) -> float:
        return sum(max(0.0, action.amount) for action in actions)

    def _variants(self, plan: Plan) -> list[Plan]:
        variants = [plan]

        for index, action in enumerate(plan.actions):
            if action.action_type not in {"migrate", "shed", "reduce_power"} or action.amount <= 0:
                continue

            for ratio in self.RATIOS:
                if ratio == 1.0:
                    continue
                actions = list(plan.actions)
                actions[index] = replace(action, amount=round(action.amount * ratio, 4))
                rationale = list(plan.rationale) + [
                    f"Optimizer candidate: scale {action.action_type} to {ratio:.0%}"
                ]
                variants.append(Plan(actions, rationale))

        return variants

    def optimize(self, world: World, plan: Plan, trace_id: str) -> tuple[Plan, dict]:
        if not plan.actions:
            return plan, {"enabled": True, "candidates": 0, "selected": "none"}

        candidates = self._variants(plan)
        evaluated: list[tuple[float, int, float, Plan]] = []

        for candidate in candidates:
            shadow = self.counterfactual.evaluate(
                world,
                candidate.actions,
                trace_id,
                horizon_ticks=2,
            )
            if not shadow.accepted:
                continue

            score_delta = float(shadow.score_delta)
            amount = self._total_amount(candidate.actions)
            evaluated.append(
                (
                    score_delta,
                    -len(candidate.actions),
                    -amount,
                    candidate,
                )
            )

        if not evaluated:
            return plan, {
                "enabled": True,
                "candidates": len(candidates),
                "accepted_candidates": 0,
                "selected": "primary",
            }

        evaluated.sort(
            key=lambda item: (item[0], item[1], item[2]),
            reverse=True,
        )
        selected = evaluated[0][3]

        return selected, {
            "enabled": True,
            "candidates": len(candidates),
            "accepted_candidates": len(evaluated),
            "selected": "primary" if selected is plan else "optimized",
            "score_delta": round(evaluated[0][0], 2),
        }
