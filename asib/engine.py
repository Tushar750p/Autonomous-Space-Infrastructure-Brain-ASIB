from .action_executor import ActionExecutor
from .counterfactual import CounterfactualEvaluator
from .decision_intelligence import DecisionIntelligence
from .mission import MissionEvaluator, MissionProfile
from .models import Action, AutonomyMode, Event, NodeStatus, World
from .optimizer import ConstrainedPlanOptimizer
from .planner import MultiNodePlanner
from .policy import SafetyPolicy
from .validation import SafetyValidator


class ASIBBrain:
    """Autonomous controller for the ASIB Earth-based digital twin."""

    def __init__(self, mission_profile: MissionProfile | None = None):
        self.policy = SafetyPolicy()
        self.mission = MissionEvaluator(mission_profile)
        self.planner = MultiNodePlanner(self.policy)
        self.validator = SafetyValidator()
        self.executor = ActionExecutor(self.policy, self.validator)
        self.counterfactual = CounterfactualEvaluator(self.executor, self.validator, self.mission)
        self.optimizer = ConstrainedPlanOptimizer(self.counterfactual)

    def observe(self, world: World) -> list[Event]:
        events: list[Event] = []
        for node in world.nodes.values():
            if node.status == NodeStatus.ISOLATED:
                # Isolation is deliberate containment. A restored network is the
                # explicit recovery signal that allows normal status evaluation.
                if not node.network_ok:
                    continue
                events.append(Event(
                    world.tick,
                    "network_recovery",
                    node.node_id,
                    "Network coordination restored; leaving isolated state",
                    "info",
                ))
                node.status = NodeStatus.DEGRADED
            if node.temperature_c >= self.policy.THERMAL_CRITICAL or node.power_pct <= self.policy.POWER_CRITICAL:
                node.status = NodeStatus.CRITICAL
                events.append(Event(world.tick, "critical", node.node_id,
                                    "Critical infrastructure condition detected", "critical"))
            elif node.temperature_c >= self.policy.THERMAL_DEGRADED or node.power_pct <= self.policy.POWER_LOW or not node.network_ok:
                node.status = NodeStatus.DEGRADED
                events.append(Event(world.tick, "degradation", node.node_id,
                                    "Infrastructure degradation detected", "warning"))
            elif node.status != NodeStatus.ISOLATED:
                node.status = NodeStatus.NOMINAL
        world.autonomy_mode = self.policy.mode_for(world)
        if not world.earth_contact_available:
            events.append(Event(
                world.tick,
                "earth_contact",
                "earth",
                "Earth contact unavailable; continuing local autonomy",
                "warning",
            ))
        return events

    def execute(self, world: World, actions: list[Action], trace_id: str) -> list[Event]:
        return self.executor.execute(world, actions, trace_id)

    def verify(self, world: World, actions: list[Action], execution_events: list[Event], trace_id: str) -> list[Event]:
        results: list[Event] = []
        executed_types = {
            (event.node_id, event.action)
            for event in execution_events
            if event.event_type == "action"
        }
        invariant_report = self.validator.validate(world)

        for action in actions:
            if (action.source_node, action.action_type) not in executed_types:
                results.append(Event(
                    world.tick,
                    "verification",
                    action.source_node,
                    "Action not verified because execution did not occur",
                    "warning",
                    action.action_type,
                    trace_id,
                ))
                continue

            node = world.nodes[action.source_node]
            safe = invariant_report.safe

            if action.action_type == "migrate" and action.target_node:
                target = world.nodes[action.target_node]
                safe = (
                    safe
                    and node.workload >= node.critical_workload
                    and target.cpu_load <= 100.0
                )
            elif action.action_type in {"shed", "reduce_power"}:
                safe = safe and node.workload >= node.critical_workload
            elif action.action_type == "isolate":
                safe = safe and (not node.network_ok) and node.status == NodeStatus.ISOLATED

            status = "verified" if safe else "not_verified"
            results.append(Event(
                world.tick,
                "verification",
                node.node_id,
                f"Action verification: {status}",
                "info" if safe else "critical",
                action.action_type,
                trace_id,
            ))
        return results

    def step(self, world: World, knowledge=None) -> list[Event]:
        trace_id = f"T{world.tick + 1:05d}"
        observed = self.observe(world)
        plan = self.planner.plan(world, knowledge=knowledge)
        plan, optimization = self.optimizer.optimize(world, plan, trace_id)

        shadow = self.counterfactual.evaluate(world, plan.actions, trace_id)
        shadow_event = None
        repair_event = None
        needs_human_review = False

        if plan.actions and not shadow.accepted:
            shadow_event = Event(
                world.tick,
                "shadow_reject",
                "planner",
                "Primary plan rejected by counterfactual safety evaluation",
                "critical",
                trace_id=trace_id,
            )

            fallback = self.planner.fallback_plan(world)
            fallback_shadow = self.counterfactual.evaluate(
                world,
                fallback.actions,
                trace_id,
                horizon_ticks=1,
            )

            if fallback.actions and fallback_shadow.accepted:
                plan = fallback
                shadow = fallback_shadow
                repair_event = Event(
                    world.tick,
                    "plan_repair",
                    "planner",
                    "Primary plan replaced by migration-free emergency fallback",
                    "warning",
                    trace_id=trace_id,
                )
                execution_events = self.execute(world, plan.actions, trace_id)
            else:
                needs_human_review = True
                execution_events = []
        else:
            execution_events = self.execute(world, plan.actions, trace_id)

        if world.autonomy_mode == AutonomyMode.SAFE and not plan.actions:
            needs_human_review = True

        review_event = None
        if needs_human_review:
            review_event = Event(
                world.tick,
                "human_review",
                "planner",
                "Human review recommended: autonomous system is holding or rejected its plan",
                "warning",
                trace_id=trace_id,
            )

        verified = self.verify(
            world,
            plan.actions if shadow.accepted else [],
            execution_events,
            trace_id,
        )

        history = (
            observed
            + ([shadow_event] if shadow_event else [])
            + ([repair_event] if repair_event else [])
            + ([review_event] if review_event else [])
            + execution_events
            + verified
        )
        world.memory.extend(history)

        decision_class = (
            "escalate" if needs_human_review
            else "repair" if repair_event
            else "act" if plan.actions
            else "hold"
        )
        invariant_safe = self.validator.validate(world).safe
        decision_quality = DecisionIntelligence.assess(
            actions=plan.actions,
            shadow=shadow,
            invariant_safe=invariant_safe,
            decision_class=decision_class,
            needs_human_review=needs_human_review,
        )

        decision = {
            "trace_id": trace_id,
            "tick": world.tick,
            "mode": world.autonomy_mode.value,
            "rationale": plan.rationale,
            "actions": [action.__dict__ for action in plan.actions],
            "executed": [event.message for event in execution_events],
            "verified": [event.message for event in verified],
            "invariants_safe": invariant_safe,
            "shadow": shadow.as_dict(),
            "optimization": optimization,
            "decision_class": decision_class,
            "plan_source": "fallback" if repair_event else "primary",
            "needs_human_review": needs_human_review,
            "decision_intelligence": decision_quality.as_dict(),
        }
        world.decision_log.append(decision)
        world.audit_ledger.append(decision)
        return history
