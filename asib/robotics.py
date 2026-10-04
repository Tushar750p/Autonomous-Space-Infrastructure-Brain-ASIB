from dataclasses import dataclass, field
from enum import Enum

from .models import Event, World


class RobotStatus(str, Enum):
    IDLE = "idle"
    TRAVELING = "traveling"
    SERVICING = "servicing"
    SAFE = "safe"
    FAILED = "failed"


@dataclass
class Robot:
    robot_id: str
    location: str
    status: RobotStatus = RobotStatus.IDLE
    battery_pct: float = 100.0
    target_node: str | None = None
    task_ticks: int = 0


@dataclass
class RobotTask:
    robot_id: str
    node_id: str
    task: str
    priority: int = 1


class RobotFleet:
    """Safe maintenance-robot simulator. No real robot interfaces are used."""

    def __init__(self, world: World):
        self.world = world
        self.robots: dict[str, Robot] = {
            "maintenance-01": Robot("maintenance-01", "service-bay"),
            "maintenance-02": Robot("maintenance-02", "service-bay"),
        }
        self.queue: list[RobotTask] = []

    def enqueue(self, node_id: str, task: str = "inspect", priority: int = 1):
        available = next((r for r in self.robots.values() if r.status == RobotStatus.IDLE), None)
        if available:
            self.queue.append(RobotTask(available.robot_id, node_id, task, priority))

    def dispatch(self) -> list[Event]:
        events: list[Event] = []
        self.queue.sort(key=lambda item: item.priority, reverse=True)

        for task in list(self.queue):
            robot = self.robots[task.robot_id]
            if robot.status != RobotStatus.IDLE or robot.battery_pct < 20:
                continue
            robot.status = RobotStatus.TRAVELING
            robot.target_node = task.node_id
            robot.task_ticks = 1
            self.queue.remove(task)
            events.append(Event(
                self.world.tick, "robot_dispatch", task.node_id,
                f"{robot.robot_id} dispatched for {task.task}", "info"
            ))
        return events

    def step(self) -> list[Event]:
        events: list[Event] = []
        for robot in self.robots.values():
            if robot.status == RobotStatus.TRAVELING:
                robot.task_ticks -= 1
                robot.battery_pct = max(0.0, robot.battery_pct - 2.0)
                if robot.task_ticks <= 0:
                    robot.status = RobotStatus.SERVICING
                    robot.task_ticks = 1
                    events.append(Event(
                        self.world.tick, "robot_arrival", robot.target_node or "unknown",
                        f"{robot.robot_id} arrived at maintenance target", "info"
                    ))
            elif robot.status == RobotStatus.SERVICING:
                robot.task_ticks -= 1
                robot.battery_pct = max(0.0, robot.battery_pct - 4.0)
                if robot.task_ticks <= 0:
                    target = self.world.nodes.get(robot.target_node or "")
                    if target:
                        target.temperature_c = max(30.0, target.temperature_c - 12.0)
                        target.network_ok = True
                    events.append(Event(
                        self.world.tick, "robot_service", robot.target_node or "unknown",
                        f"{robot.robot_id} completed simulated maintenance", "info"
                    ))
                    robot.status = RobotStatus.IDLE
                    robot.target_node = None
            elif robot.battery_pct <= 15 and robot.status == RobotStatus.IDLE:
                robot.status = RobotStatus.SAFE
                events.append(Event(
                    self.world.tick, "robot_low_power", robot.robot_id,
                    "Robot entered safe state due to low battery", "warning"
                ))
        return events
