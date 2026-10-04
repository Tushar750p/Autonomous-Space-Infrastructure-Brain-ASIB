from dataclasses import dataclass
from .models import Event, World


@dataclass
class Message:
    source: str
    destination: str
    payload: str
    available_at_tick: int


class CommunicationModel:
    """Simulates delayed message availability in the digital twin."""

    def send(self, world: World, source: str, destination: str, payload: str) -> Message:
        delay_ticks = max(0, round(world.comms_delay_s))
        return Message(source, destination, payload, world.tick + delay_ticks)

    def deliver(self, world: World, message: Message) -> Event | None:
        if world.tick < message.available_at_tick:
            return None
        return Event(
            world.tick,
            "communication",
            message.destination,
            f"Message delivered from {message.source}: {message.payload}",
            "info",
        )
