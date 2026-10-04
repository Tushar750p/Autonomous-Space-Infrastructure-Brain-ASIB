from .mission import MissionEvaluator
from .runtime import ASIBRuntime
from .scorecard import RecoveryScorecardBuilder
from .simulator import Simulator


def _is_safe_recovery(runtime: ASIBRuntime) -> bool:
    for node in runtime.world.nodes.values():
        if node.temperature_c >= 85.0 or node.power_pct <= 15.0:
            return False
    return True


def run_compound_benchmark(ticks: int = 20) -> dict:
    sim = Simulator()
    sim.inject_thermal_failure("orbital-node-01", 98)
    sim.inject_power_failure("orbital-node-02", 18)
    sim.inject_network_failure("orbital-node-03")
    sim.world.nodes["orbital-node-03"].critical_workload = 0
    sim.inject_comms_delay(5.0)

    runtime = ASIBRuntime(sim)
    evaluator = MissionEvaluator()
    initial_score = evaluator.evaluate(sim.world)["score"]
    reports = []
    score_trajectory = []
    recovery_tick = None
    action_count = 0
    unsafe_event_count = 0

    for report in runtime.run(ticks):
        reports.append(report)
        score_trajectory.append(evaluator.evaluate(sim.world)["score"])

        for event in report.events:
            if event.get("event_type") == "action":
                action_count += 1
            if event.get("event_type") in {"blocked_action", "verification"} and (
                event.get("event_type") == "blocked_action"
                or "not verified" in event.get("message", "")
                or "not_verified" in event.get("message", "")
            ):
                unsafe_event_count += 1

        if recovery_tick is None and _is_safe_recovery(runtime):
            recovery_tick = report.tick

    final = evaluator.evaluate(sim.world)
    scorecard = RecoveryScorecardBuilder.build(reports, recovery_tick)
    return {
        "ticks": ticks,
        "initial_score": initial_score,
        "final_mission": final,
        "score_delta": round(final["score"] - initial_score, 2),
        "average_score": round(sum(score_trajectory) / len(score_trajectory), 2) if score_trajectory else initial_score,
        "recovery_tick": recovery_tick,
        "action_count": action_count,
        "unsafe_event_count": unsafe_event_count,
        "recovery_scorecard": scorecard.as_dict(),
        "memory_entries": len(sim.world.memory),
        "knowledge_summary": runtime.knowledge.summary(sim.world),
        "robot_states": {k: v.__dict__ for k, v in runtime.robots.robots.items()},
        "reports": reports,
    }
