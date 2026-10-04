from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetrySample:
    tick: int
    temperature_c: float
    power_pct: float
    cpu_load: float
    workload: float
    network_ok: bool


class TelemetryRecorder:
    """Stores compact, deterministic telemetry history for prediction and replay."""

    def record(self, world) -> None:
        for node in world.nodes.values():
            history = world.telemetry.setdefault(node.node_id, [])
            history.append(TelemetrySample(
                tick=world.tick,
                temperature_c=round(node.temperature_c, 4),
                power_pct=round(node.power_pct, 4),
                cpu_load=round(node.cpu_load, 4),
                workload=round(node.workload, 4),
                network_ok=node.network_ok,
            ))
            del history[:-200]

    def latest(self, world, node_id: str):
        history = world.telemetry.get(node_id, [])
        return history[-1] if history else None
