from dataclasses import dataclass, field

from .comms import CommunicationModel, Message
from .engine import ASIBBrain
from .models import Event, World
from .predictor import RiskPredictor
from .robotics import RobotFleet
from .simulator import Simulator


@dataclass
class RuntimeReport:
    tick: int
    events: list[dict]
    risks: list[dict]
    state: dict
    memory_entries: int


class ASIBRuntime:
    """Closed-loop Earth testbed runtime: physics -> brain -> robots -> telemetry."""

    def __init__(self, simulator: Simulator | None = None):
        self.simulator = simulator or Simulator()
        self.world: World = self.simulator.world
        self.brain = ASIBBrain()
        self.predictor = RiskPredictor()
        self.comms = CommunicationModel()
        self.robots = RobotFleet(self.world)
        self.inbox: list[Message] = []
        self.history: list[Event] = []

    def tick(self) -> RuntimeReport:
        self.simulator.advance_physics()
        events = self.brain.step(self.world)

        risks = self.predictor.predict(self.world)
        for risk in risks:
            if risk.score >= 60 and self.world.nodes[risk.node_id].critical_workload <= 0:
                self.robots.enqueue(risk.node_id, "inspect-and-service", priority=10)

        events += self.robots.dispatch()
        events += self.robots.step()

        for event in events:
            self.history.append(event)

        self.world.memory.extend(events)
        return RuntimeReport(
            tick=self.world.tick,
            events=[e.__dict__ for e in events],
            risks=[r.__dict__ for r in risks],
            state=self.simulator.snapshot(),
            memory_entries=len(self.world.memory),
        )

    def queue_message(self, source: str, destination: str, payload: str):
        self.inbox.append(self.comms.send(self.world, source, destination, payload))

    def deliver_messages(self) -> list[Event]:
        delivered: list[Event] = []
        pending: list[Message] = []
        for message in self.inbox:
            event = self.comms.deliver(self.world, message)
            if event is None:
                pending.append(message)
            else:
                delivered.append(event)
        self.inbox = pending
        self.world.memory.extend(delivered)
        self.history.extend(delivered)
        return delivered

    def run(self, ticks: int = 10) -> list[RuntimeReport]:
        reports = []
        for _ in range(max(0, ticks)):
            reports.append(self.tick())
            self.deliver_messages()
        return reports
