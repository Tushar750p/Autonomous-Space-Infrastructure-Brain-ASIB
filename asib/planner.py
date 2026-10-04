from dataclasses import dataclass

from .models import Action, AutonomyMode, World
from .network import NetworkModel
from .policy import SafetyPolicy


@dataclass
class Plan:
    actions: list[Action]
    rationale: list[str]


class MultiNodePlanner:
    """Deterministic, safety-first planner for distributed recovery."""

    def __init__(self, policy: SafetyPolicy | None = None):
        self.policy = policy or SafetyPolicy()
        self.network = NetworkModel()

    def plan(self, world: World) -> Plan:
        actions: list[Action] = []
        rationale: list[str] = []

        for source in world.nodes.values():
            unhealthy = (
                source.temperature_c >= self.policy.THERMAL_DEGRADED
                or source.power_pct <= self.policy.POWER_LOW
                or not source.network_ok
            )
            if not unhealthy:
                continue

            movable = max(0.0, source.workload - source.critical_workload)
            targets = sorted(
                (
                    n for n in world.nodes.values()
                    if n.node_id != source.node_id
                    and n.network_ok
                    and self.network.is_connected(world, source.node_id, n.node_id)
                    and n.temperature_c < self.policy.THERMAL_DEGRADED
                    and n.power_pct > self.policy.POWER_LOW
                    and n.free_cpu >= 5.0
                ),
                key=lambda n: (n.temperature_c, -n.free_cpu),
            )

            if movable > 0 and targets:
                target = targets[0]
                amount = min(movable, target.free_cpu, self.policy.MAX_MIGRATION)
                candidate = Action(
                    "migrate", source.node_id, target.node_id, amount,
                    "preserve critical workload while relieving an unhealthy node",
                )
                if self.policy.allow(world, candidate):
                    actions.append(candidate)
                    rationale.append(
                        f"Migrate {amount:.1f} workload from {source.node_id} to {target.node_id}"
                    )

            if source.temperature_c >= self.policy.THERMAL_CRITICAL or source.power_pct <= self.policy.POWER_CRITICAL:
                shed_amount = min(movable, 25.0)
                if shed_amount > 0:
                    candidate = Action("shed", source.node_id, amount=shed_amount,
                                       reason="protect node safety margins")
                    if self.policy.allow(world, candidate):
                        actions.append(candidate)
                        rationale.append(
                            f"Shed {shed_amount:.1f} non-critical workload on {source.node_id}"
                        )

            if source.power_pct <= self.policy.POWER_LOW:
                candidate = Action("reduce_power", source.node_id, amount=15.0,
                                   reason="enter power conservation")
                if self.policy.allow(world, candidate):
                    actions.append(candidate)
                    rationale.append(f"Reduce power load on {source.node_id}")

            if not source.network_ok:
                candidate = Action("isolate", source.node_id,
                                   reason="contain a network-isolated node")
                if self.policy.allow(world, candidate):
                    actions.append(candidate)
                    rationale.append(f"Isolate {source.node_id} from coordination")

        if not actions and world.autonomy_mode == AutonomyMode.SAFE:
            rationale.append("No safe autonomous action found; hold state")

        return Plan(actions, rationale)
