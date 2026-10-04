from dataclasses import dataclass

from .comms import CommunicationModel, Message
from .distributed import DistributedKnowledge
from .engine import ASIBBrain
from .models import Event, World
from .predictor import RiskPredictor
from .robotics import RobotFleet
from .simulator import Simulator
from .telemetry import TelemetryRecorder


@dataclass
class RuntimeReport:
    tick: int
    events: list[dict]
    risks: list[dict]
    state: dict
    memory_entries: int
    knowledge: dict


class ASIBRuntime:
    """Closed-loop Earth testbed: physics -> knowledge -> brain -> robots -> verification."""

    def __init__(self, simulator: Simulator | None = None):
        self.simulator = simulator or Simulator()
        self.world: World = self.simulator.world
        self.brain = ASIBBrain()
        self.predictor = RiskPredictor()
        self.telemetry = TelemetryRecorder()
        self.comms = CommunicationModel()
        self.knowledge = DistributedKnowledge(self.world)
        self.knowledge.prime()
        self.robots = RobotFleet(self.world)
        self.inbox: list[Message] = []
        self.history: list[Event] = []

    def tick(self) -> RuntimeReport:
        self.simulator.advance_physics()
        self.telemetry.record(self.world)

        knowledge_events = self.knowledge.sync(self.world)
        brain_events = self.brain.step(self.world, knowledge=self.knowledge)
        risks = self.predictor.predict(self.world)

        for risk in risks:
            if risk.score >= 70:
                node = self.world.nodes[risk.node_id]
                if node.status.value not in {"isolated"}:
                    self.robots.enqueue(risk.node_id, "inspect-and-service", priority=10)

        robot_events = self.robots.dispatch()
        robot_events += self.robots.step()

        events = knowledge_events + brain_events + robot_events
        self.history.extend(events)

        # Brain events are already persisted inside ASIBBrain.step(). Only
        # persist the auxiliary knowledge/robot events here to avoid duplicates.
        self.world.memory.extend(knowledge_events + robot_events)

        return RuntimeReport(
            tick=self.world.tick,
            events=[e.__dict__ for e in events],
            risks=[r.__dict__ for r in risks],
            state=self.simulator.snapshot(),
            memory_entries=len(self.world.memory),
            knowledge=self.knowledge.summary(self.world),
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
        reports: list[RuntimeReport] = []
        for _ in range(max(0, ticks)):
            reports.append(self.tick())
            self.deliver_messages()
        return reports

    def reset(self):
        self.__init__(Simulator())
