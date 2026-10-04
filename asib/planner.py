from dataclasses import dataclass

from .models import Action, AutonomyMode, World
from .network import NetworkModel
from .policy import SafetyPolicy
from .resources import ResourceReservationBook


@dataclass
class Plan:
    actions: list[Action]
    rationale: list[str]


class MultiNodePlanner:
    """Deterministic, safety-first planner for distributed recovery."""

    def __init__(self, policy: SafetyPolicy | None = None):
        self.policy = policy or SafetyPolicy()
        self.network = NetworkModel()

    def plan(self, world: World, knowledge=None) -> Plan:
        actions: list[Action] = []
        rationale: list[str] = []
        reservations = ResourceReservationBook.create()

        def local_snapshot(node):
            return {
                "node_id": node.node_id,
                "cpu_capacity": node.cpu_capacity,
                "cpu_load": node.cpu_load,
                "temperature_c": node.temperature_c,
                "power_pct": node.power_pct,
                "network_ok": node.network_ok,
                "latency_ms": node.latency_ms,
                "workload": node.workload,
                "critical_workload": node.critical_workload,
                "status": node.status.value,
            }

        def estimate(observer_id: str, node):
            if knowledge is None:
                return local_snapshot(node), 0, 1.0
            item = knowledge.estimate(observer_id, node.node_id, world)
            if item.snapshot is None:
                return local_snapshot(node), item.age_ticks, item.confidence
            return item.snapshot, item.age_ticks, item.confidence

        for source in world.nodes.values():
            unhealthy = (
                source.temperature_c >= self.policy.THERMAL_DEGRADED
                or source.power_pct <= self.policy.POWER_LOW
                or not source.network_ok
            )
            if not unhealthy:
                continue

            movable = max(0.0, source.workload - source.critical_workload)
            remaining = movable
            targets = []

            for candidate in world.nodes.values():
                if candidate.node_id == source.node_id:
                    continue
                if not candidate.network_ok or not self.network.is_connected(world, source.node_id, candidate.node_id):
                    continue

                estimated, age, confidence = estimate(source.node_id, candidate)
                if confidence < 0.20:
                    rationale.append(
                        f"Skip {candidate.node_id} for {source.node_id}: insufficient state confidence"
                    )
                    continue

                estimated_temp = float(estimated["temperature_c"])
                estimated_power = float(estimated["power_pct"])
                estimated_cpu = float(estimated["cpu_load"])
                estimated_free_cpu = max(
                    0.0, float(estimated.get("cpu_capacity", candidate.cpu_capacity)) - estimated_cpu
                )

                if estimated_temp >= self.policy.THERMAL_DEGRADED or estimated_power <= self.policy.POWER_LOW:
                    continue
                if estimated_free_cpu < 5.0 or reservations.available_cpu(candidate.node_id, candidate) < 5.0:
                    continue

                # Uncertain state is deliberately penalized so stale nodes are not
                # selected merely because they look good in an old snapshot.
                uncertainty_penalty = (1.0 - confidence) * 20.0
                score = estimated_temp + uncertainty_penalty - min(estimated_free_cpu, 100.0) * 0.12
                targets.append((score, age, candidate, confidence))

            targets.sort(key=lambda item: (item[0], -item[3], item[1], item[2].node_id))

            if movable > 0 and targets:
                _, age, target, confidence = targets[0]
                amount = min(
                    movable,
                    target.free_cpu,
                    reservations.available_cpu(target.node_id, target),
                    self.policy.MAX_MIGRATION,
                )
                candidate = Action(
                    "migrate",
                    source.node_id,
                    target.node_id,
                    amount,
                    "preserve critical workload while relieving an unhealthy node",
                    age,
                    confidence,
                )
                if self.policy.allow(world, candidate) and reservations.reserve_cpu(target.node_id, target, amount):
                    actions.append(candidate)
                    remaining = max(0.0, remaining - amount)
                    rationale.append(
                        f"Migrate {amount:.1f} workload from {source.node_id} to {target.node_id} "
                        f"(confidence={confidence:.2f}, age={age}t)"
                    )

            if source.temperature_c >= self.policy.THERMAL_CRITICAL or source.power_pct <= self.policy.POWER_CRITICAL:
                shed_amount = min(remaining, 25.0)
                if shed_amount > 0:
                    candidate = Action("shed", source.node_id, amount=shed_amount,
                                       reason="protect node safety margins")
                    if self.policy.allow(world, candidate):
                        actions.append(candidate)
                        remaining = max(0.0, remaining - shed_amount)
                        rationale.append(
                            f"Shed {shed_amount:.1f} non-critical workload on {source.node_id}"
                        )

            if source.power_pct <= self.policy.POWER_LOW and remaining > 0:
                power_amount = min(15.0, remaining)
                candidate = Action("reduce_power", source.node_id, amount=power_amount,
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
