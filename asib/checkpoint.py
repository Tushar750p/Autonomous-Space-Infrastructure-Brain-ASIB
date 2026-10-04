from __future__ import annotations

import json
from pathlib import Path

from .audit import DecisionLedger
from .environment import OrbitalEnvironment
from .models import AutonomyMode, Event, Node, NodeStatus, World


FORMAT_VERSION = 1


def export_world(world: World) -> dict:
    """Return a complete JSON-safe operational checkpoint for the simulation world."""
    return {
        "format_version": FORMAT_VERSION,
        "tick": world.tick,
        "autonomy_mode": world.autonomy_mode.value,
        "comms_delay_s": world.comms_delay_s,
        "global_power_budget_pct": world.global_power_budget_pct,
        "earth_contact_available": world.earth_contact_available,
        "links": dict(world.links),
        "environment": world.environment.snapshot(),
        "nodes": {
            node_id: {
                "node_id": node.node_id,
                "cpu_capacity": node.cpu_capacity,
                "cpu_load": node.cpu_load,
                "temperature_c": node.temperature_c,
                "power_pct": node.power_pct,
                "storage_pct": node.storage_pct,
                "network_ok": node.network_ok,
                "latency_ms": node.latency_ms,
                "workload": node.workload,
                "critical_workload": node.critical_workload,
                "status": node.status.value,
            }
            for node_id, node in world.nodes.items()
        },
        "memory": [event.__dict__ for event in world.memory],
        "decision_log": list(world.decision_log),
        "audit_ledger": world.audit_ledger.export(),
    }


def restore_world(payload: dict) -> World:
    if int(payload.get("format_version", 0)) != FORMAT_VERSION:
        raise ValueError("Unsupported ASIB checkpoint format")

    environment_data = payload.get("environment", {})
    environment = OrbitalEnvironment(
        phase_deg=float(environment_data.get("phase_deg", 0.0)),
    )

    nodes = {}
    for node_id, data in payload.get("nodes", {}).items():
        node = Node(
            node_id=str(data.get("node_id", node_id)),
            cpu_capacity=float(data.get("cpu_capacity", 100.0)),
            cpu_load=float(data.get("cpu_load", 0.0)),
            temperature_c=float(data.get("temperature_c", 45.0)),
            power_pct=float(data.get("power_pct", 80.0)),
            storage_pct=float(data.get("storage_pct", 25.0)),
            network_ok=bool(data.get("network_ok", True)),
            latency_ms=float(data.get("latency_ms", 40.0)),
            workload=float(data.get("workload", 60.0)),
            critical_workload=float(data.get("critical_workload", 20.0)),
            status=NodeStatus(data.get("status", NodeStatus.NOMINAL.value)),
        )
        nodes[node_id] = node

    memory = [
        Event(
            tick=int(event["tick"]),
            event_type=str(event["event_type"]),
            node_id=str(event["node_id"]),
            message=str(event["message"]),
            severity=str(event.get("severity", "info")),
            action=event.get("action"),
            trace_id=event.get("trace_id"),
        )
        for event in payload.get("memory", [])
    ]

    return World(
        nodes=nodes,
        memory=memory,
        decision_log=list(payload.get("decision_log", [])),
        links=dict(payload.get("links", {})),
        tick=int(payload.get("tick", 0)),
        autonomy_mode=AutonomyMode(payload.get("autonomy_mode", AutonomyMode.NORMAL.value)),
        comms_delay_s=float(payload.get("comms_delay_s", 0.2)),
        global_power_budget_pct=float(payload.get("global_power_budget_pct", 100.0)),
        earth_contact_available=bool(payload.get("earth_contact_available", True)),
        audit_ledger=DecisionLedger.from_export(payload.get("audit_ledger", [])),
        environment=environment,
    )


def to_json(world: World) -> str:
    return json.dumps(export_world(world), sort_keys=True, indent=2, default=str)


def save(world: World, path: str) -> str:
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(to_json(world), encoding="utf-8")
    return str(destination)


def load(path: str) -> World:
    source = Path(path).expanduser()
    return restore_world(json.loads(source.read_text(encoding="utf-8")))
