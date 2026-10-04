from dataclasses import dataclass

from .models import NodeStatus, World


@dataclass(frozen=True)
class InvariantViolation:
    node_id: str
    invariant: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    safe: bool
    violations: list[InvariantViolation]


class SafetyValidator:
    """Checks post-action invariants that must hold in every simulation tick."""

    THERMAL_HARD_LIMIT = 110.0
    POWER_HARD_FLOOR = 0.0
    CPU_HARD_LIMIT = 100.0
    CRITICAL_WORKLOAD_TOLERANCE = 1e-9

    def validate(self, world: World) -> ValidationReport:
        violations: list[InvariantViolation] = []

        for node in world.nodes.values():
            if node.temperature_c > self.THERMAL_HARD_LIMIT:
                violations.append(InvariantViolation(
                    node.node_id, "thermal_hard_limit",
                    f"temperature {node.temperature_c:.2f}C exceeds {self.THERMAL_HARD_LIMIT:.1f}C",
                ))
            if node.power_pct < self.POWER_HARD_FLOOR:
                violations.append(InvariantViolation(
                    node.node_id, "power_floor",
                    f"power {node.power_pct:.2f}% is below zero",
                ))
            if node.cpu_load < 0 or node.cpu_load > self.CPU_HARD_LIMIT:
                violations.append(InvariantViolation(
                    node.node_id, "cpu_bounds",
                    f"cpu load {node.cpu_load:.2f}% is outside [0, 100]",
                ))
            if node.workload < node.critical_workload - self.CRITICAL_WORKLOAD_TOLERANCE:
                violations.append(InvariantViolation(
                    node.node_id, "critical_workload_preservation",
                    f"workload {node.workload:.2f} is below critical floor {node.critical_workload:.2f}",
                ))
            if node.status == NodeStatus.ISOLATED and node.network_ok:
                violations.append(InvariantViolation(
                    node.node_id, "isolation_consistency",
                    "node is marked isolated while network_ok is true",
                ))

        return ValidationReport(safe=not violations, violations=violations)
