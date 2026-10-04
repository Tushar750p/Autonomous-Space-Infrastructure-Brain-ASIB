from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class NodeStatus(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    ISOLATED = "isolated"


class AutonomyMode(str, Enum):
    NORMAL = "normal"
    CONSERVATION = "conservation"
    SAFE = "safe"


@dataclass
class Node:
    node_id: str
    cpu_capacity: float = 100.0
    cpu_load: float = 35.0
    temperature_c: float = 45.0
    power_pct: float = 80.0
    storage_pct: float = 25.0
    network_ok: bool = True
    latency_ms: float = 40.0
    workload: float = 60.0
    critical_workload: float = 20.0
    status: NodeStatus = NodeStatus.NOMINAL

    @property
    def free_cpu(self) -> float:
        return max(0.0, self.cpu_capacity - self.cpu_load)


@dataclass
class Event:
    tick: int
    event_type: str
    node_id: str
    message: str
    severity: str = "info"
    action: str | None = None
    trace_id: str | None = None


@dataclass
class Action:
    action_type: str
    source_node: str
    target_node: str | None = None
    amount: float = 0.0
    reason: str = ""
    knowledge_age: int = 0
    knowledge_confidence: float = 1.0


@dataclass
class World:
    nodes: Dict[str, Node] = field(default_factory=dict)
    memory: List[Event] = field(default_factory=list)
    telemetry: Dict[str, list] = field(default_factory=dict)
    decision_log: List[dict] = field(default_factory=list)
    links: Dict[str, bool] = field(default_factory=dict)
    tick: int = 0
    autonomy_mode: AutonomyMode = AutonomyMode.NORMAL
    comms_delay_s: float = 0.2
    global_power_budget_pct: float = 100.0
    earth_contact_available: bool = True
