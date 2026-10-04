from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

class NodeStatus(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"

@dataclass
class Node:
    node_id: str
    cpu_load: float = 0.35
    temperature_c: float = 45.0
    power_pct: float = 80.0
    network_ok: bool = True
    workload: float = 60.0
    status: NodeStatus = NodeStatus.NOMINAL

@dataclass
class Event:
    event_type: str
    node_id: str
    message: str
    action: str | None = None

@dataclass
class World:
    nodes: Dict[str, Node] = field(default_factory=dict)
    memory: List[Event] = field(default_factory=list)
    tick: int = 0
