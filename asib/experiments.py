from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .mission import MissionEvaluator
from .runtime import ASIBRuntime
from .simulator import Simulator
from .policy import SafetyPolicy


@dataclass(frozen=True)
class ExperimentCase:
    name: str
    setup: Callable[[Simulator], None]


def _thermal(sim: Simulator):
    sim.inject_thermal_failure("orbital-node-01", 96)


def _power(sim: Simulator):
    sim.inject_power_failure("orbital-node-02", 18)


def _network(sim: Simulator):
    sim.world.nodes["orbital-node-03"].critical_workload = 0
    sim.inject_network_failure("orbital-node-03")


def _partition(sim: Simulator):
    sim.inject_network_partition("orbital-node-02")


def _compute(sim: Simulator):
    sim.inject_compute_overload("orbital-node-01", 45)


def _earth_loss(sim: Simulator):
    sim.inject_earth_contact_loss()


def _eclipse(sim: Simulator):
    sim.world.environment.phase_deg = 120.0
    sim.world.nodes["orbital-node-02"].power_pct = 40.0


def _eclipse_compound(sim: Simulator):
    sim.world.environment.phase_deg = 120.0
    sim.inject_thermal_failure("orbital-node-01", 96)
    sim.inject_power_failure("orbital-node-02", 40)
    sim.world.nodes["orbital-node-03"].critical_workload = 0
    sim.inject_network_failure("orbital-node-03")
    sim.inject_network_partition("orbital-node-02")
    sim.inject_comms_delay(12.0)
    sim.inject_earth_contact_loss()


def _compound(sim: Simulator):
    sim.inject_thermal_failure("orbital-node-01", 96)
    sim.inject_power_failure("orbital-node-02", 20)
    sim.world.nodes["orbital-node-03"].critical_workload = 0
    sim.inject_network_failure("orbital-node-03")
    sim.inject_network_partition("orbital-node-02")
    sim.inject_comms_delay(12.0)
    sim.inject_earth_contact_loss()


def default_experiment_suite() -> tuple[ExperimentCase, ...]:
    return (
        ExperimentCase("thermal", _thermal),
        ExperimentCase("power", _power),
        ExperimentCase("network", _network),
        ExperimentCase("partition", _partition),
        ExperimentCase("compute", _compute),
        ExperimentCase("earth-loss", _earth_loss),
        ExperimentCase("eclipse", _eclipse),
        ExperimentCase("eclipse-compound", _eclipse_compound),
        ExperimentCase("compound", _compound),
    )


def _policy_unsafe(sim: Simulator) -> bool:
    policy = SafetyPolicy()
    return any(
        node.temperature_c >= policy.THERMAL_CRITICAL
        or node.power_pct <= policy.POWER_CRITICAL
        or (not node.network_ok and node.critical_workload > 0)
        for node in sim.world.nodes.values()
    )


def _run_passive(sim: Simulator, ticks: int) -> dict:
    evaluator = MissionEvaluator()
    scores: list[float] = []
    unsafe_ticks = 0
    for _ in range(max(0, ticks)):
        sim.advance_physics()
        scores.append(evaluator.evaluate(sim.world)["score"])
        unsafe_ticks += int(_policy_unsafe(sim))
    final = evaluator.evaluate(sim.world)
    return {
        "final_score": final["score"],
        "average_score": round(sum(scores) / len(scores), 2) if scores else final["score"],
        "policy_unsafe": _policy_unsafe(sim),
        "unsafe_ticks": unsafe_ticks,
        "score_trajectory": scores,
    }


def _run_asib(sim: Simulator, ticks: int) -> dict:
    runtime = ASIBRuntime(sim)
    evaluator = MissionEvaluator()
    scores: list[float] = []
    peak_risk = 0.0
    action_count = 0
    recovery_tick = None
    unsafe_ticks = 0

    for report in runtime.run(ticks):
        score = evaluator.evaluate(sim.world)["score"]
        scores.append(score)
        peak_risk = max(peak_risk, *(risk["score"] for risk in report.risks))

        for event in report.events:
            if event.get("event_type") == "action":
                action_count += 1

        policy_unsafe = _policy_unsafe(sim)
        unsafe_ticks += int(policy_unsafe)
        if recovery_tick is None and not policy_unsafe:
            recovery_tick = report.tick

    final = evaluator.evaluate(sim.world)
    return {
        "final_score": final["score"],
        "average_score": round(sum(scores) / len(scores), 2) if scores else final["score"],
        "policy_unsafe": _policy_unsafe(sim),
        "unsafe_ticks": unsafe_ticks,
        "peak_risk": round(peak_risk, 2),
        "action_count": action_count,
        "recovery_tick": recovery_tick,
        "knowledge": runtime.knowledge.summary(sim.world),
    }


def run_experiment_suite(ticks: int = 20) -> dict:
    results = []

    for case in default_experiment_suite():
        passive_sim = Simulator()
        asib_sim = Simulator()
        case.setup(passive_sim)
        case.setup(asib_sim)

        passive = _run_passive(passive_sim, ticks)
        active = _run_asib(asib_sim, ticks)

        results.append({
            "scenario": case.name,
            "ticks": ticks,
            "passive": passive,
            "asib": active,
            "score_improvement": round(active["final_score"] - passive["final_score"], 2),
            "safety_delta": int(not active["policy_unsafe"]) - int(not passive["policy_unsafe"]),
        })

    return {
        "suite_version": "1.1",
        "ticks": ticks,
        "deterministic": True,
        "scenarios": results,
    }
