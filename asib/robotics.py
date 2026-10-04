from dataclasses import dataclass
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
        if node_id not in self.world.nodes:
            return False
        if any(item.node_id == node_id for item in self.queue):
            return False
        if any(robot.target_node == node_id for robot in self.robots.values()):
            return False
        available = next((r for r in self.robots.values() if r.status == RobotStatus.IDLE), None)
        if available is None:
            return False
        self.queue.append(RobotTask(available.robot_id, node_id, task, priority))
        return True

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
                    target_id = robot.target_node
                    target = self.world.nodes.get(target_id or "")
                    if target:
                        repairs = []
                        if target.temperature_c >= 70.0:
                            target.temperature_c = max(30.0, target.temperature_c - 12.0)
                            repairs.append("thermal")
                        if target.power_pct <= 30.0:
                            target.power_pct = min(100.0, target.power_pct + 20.0)
                            repairs.append("power")
                        if not target.network_ok:
                            target.network_ok = True
                            repairs.append("network")
                        if not repairs:
                            repairs.append("inspection")
                    events.append(Event(
                        self.world.tick, "robot_service", target_id or "unknown",
                        f"{robot.robot_id} completed simulated maintenance ({', '.join(repairs)})", "info"
                    ))
                    robot.status = RobotStatus.IDLE
                    robot.target_node = None

            if robot.battery_pct <= 15 and robot.status == RobotStatus.IDLE:
                robot.status = RobotStatus.SAFE
                events.append(Event(
                    self.world.tick, "robot_low_power", robot.robot_id,
                    "Robot entered safe state due to low battery", "warning"
                ))
        return events

    def recharge(self, robot_id: str | None = None):
        robots = self.robots.values() if robot_id is None else [self.robots[robot_id]]
        for robot in robots:
            if robot.status == RobotStatus.SAFE and robot.target_node is None:
                robot.battery_pct = min(100.0, robot.battery_pct + 50.0)
                if robot.battery_pct > 20:
                    robot.status = RobotStatus.IDLE
