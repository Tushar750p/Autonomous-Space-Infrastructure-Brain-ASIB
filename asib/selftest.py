from __future__ import annotations

from .benchmark import run_compound_benchmark
from .experiments import run_experiment_suite
from .mission import MissionEvaluator
from .runtime import ASIBRuntime
from .validation import SafetyValidator


def run_selftest(ticks: int = 5) -> dict:
    checks: dict[str, bool] = {}

    runtime = ASIBRuntime()
    reports = runtime.run(max(1, ticks))
    checks["runtime_progress"] = runtime.world.tick == max(1, ticks)
    checks["telemetry"] = all(
        len(history) >= max(1, ticks)
        for history in runtime.world.telemetry.values()
    )
    checks["audit_chain"] = runtime.world.audit_ledger.verify()
    checks["replay_journal"] = runtime.replay.validate()
    checks["safety_invariants"] = SafetyValidator().validate(runtime.world).safe

    mission = MissionEvaluator().evaluate(runtime.world)
    checks["mission_score_bounds"] = 0.0 <= mission["score"] <= 100.0

    benchmark = run_compound_benchmark(max(1, ticks))
    checks["benchmark_bounds"] = 0.0 <= benchmark["final_mission"]["score"] <= 100.0
    checks["benchmark_audit"] = benchmark["knowledge_summary"]["known_state_pairs"] >= 0

    suite_a = run_experiment_suite(max(1, min(5, ticks)))
    suite_b = run_experiment_suite(max(1, min(5, ticks)))
    checks["experiment_determinism"] = suite_a == suite_b
    checks["experiment_coverage"] = len(suite_a["scenarios"]) >= 7

    checks["all"] = all(checks.values())

    return {
        "ticks": max(1, ticks),
        "passed": checks["all"],
        "checks": checks,
        "runtime_tick": runtime.world.tick,
        "mission": mission,
        "benchmark_recovery_tick": benchmark["recovery_tick"],
        "experiment_scenarios": [item["scenario"] for item in suite_a["scenarios"]],
    }


if __name__ == "__main__":
    import json
    import sys

    requested = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    result = run_selftest(requested)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
