from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean

from .experiments import default_experiment_suite
from .mission import MissionEvaluator
from .runtime import ASIBRuntime
from .simulator import Simulator


@dataclass(frozen=True)
class RobustnessCase:
    scenario: str
    trials: int
    ticks: int
    mean_final_score: float
    min_final_score: float
    max_final_score: float
    mean_unsafe_ticks: float
    mean_actions: float

    def as_dict(self) -> dict:
        return self.__dict__


def _perturb_initial_state(sim: Simulator, rng: random.Random) -> None:
    for node in sim.world.nodes.values():
        node.temperature_c = max(20.0, min(105.0, node.temperature_c + rng.uniform(-2.0, 2.0)))
        node.power_pct = max(1.0, min(100.0, node.power_pct + rng.uniform(-3.0, 3.0)))
        node.workload = max(node.critical_workload, min(100.0, node.workload + rng.uniform(-2.0, 2.0)))
        node.cpu_load = node.workload


def _run_trial(setup, ticks: int, rng: random.Random) -> tuple[float, int, int]:
    sim = Simulator()
    _perturb_initial_state(sim, rng)
    setup(sim)
    runtime = ASIBRuntime(sim)
    evaluator = MissionEvaluator()
    unsafe_ticks = 0
    actions = 0

    for report in runtime.run(ticks):
        if any(
            node.temperature_c >= 85.0
            or node.power_pct <= 15.0
            for node in sim.world.nodes.values()
        ):
            unsafe_ticks += 1
        actions += sum(event.get("event_type") == "action" for event in report.events)

    return evaluator.evaluate(sim.world)["score"], unsafe_ticks, actions


def run_robustness_suite(ticks: int = 10, trials: int = 10, seed: int = 20261004) -> dict:
    ticks = max(1, min(500, int(ticks)))
    trials = max(1, min(100, int(trials)))
    root_rng = random.Random(seed)
    results: list[RobustnessCase] = []

    for case in default_experiment_suite():
        scores: list[float] = []
        unsafe_ticks: list[int] = []
        actions: list[int] = []

        for _ in range(trials):
            trial_seed = root_rng.randrange(0, 2**32)
            rng = random.Random(trial_seed)
            score, unsafe, action_count = _run_trial(case.setup, ticks, rng)
            scores.append(score)
            unsafe_ticks.append(unsafe)
            actions.append(action_count)

        results.append(
            RobustnessCase(
                scenario=case.name,
                trials=trials,
                ticks=ticks,
                mean_final_score=round(mean(scores), 2),
                min_final_score=round(min(scores), 2),
                max_final_score=round(max(scores), 2),
                mean_unsafe_ticks=round(mean(unsafe_ticks), 2),
                mean_actions=round(mean(actions), 2),
            )
        )

    return {
        "suite_version": "1.0",
        "seed": seed,
        "ticks": ticks,
        "trials": trials,
        "deterministic": True,
        "scenarios": [item.as_dict() for item in results],
    }
