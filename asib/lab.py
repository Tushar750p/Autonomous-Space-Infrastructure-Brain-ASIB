from __future__ import annotations

from . import __version__
from .benchmark import run_compound_benchmark
from .experiments import run_experiment_suite
from .robustness import run_robustness_suite
from .selftest import run_selftest


def run_research_lab(
    ticks: int = 5,
    robustness_trials: int = 3,
    seed: int = 20261004,
) -> dict:
    ticks = max(1, min(100, int(ticks)))
    return {
        "version": __version__,
        "selftest": run_selftest(ticks),
        "benchmark": run_compound_benchmark(ticks),
        "experiments": run_experiment_suite(ticks),
        "robustness": run_robustness_suite(
            ticks=min(ticks, 10),
            trials=max(1, min(20, int(robustness_trials))),
            seed=seed,
        ),
    }
