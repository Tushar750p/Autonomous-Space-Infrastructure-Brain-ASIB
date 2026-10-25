"""APSE Rover 2D grid-world research prototype.

Simulation only: not flight software and not a physical robot controller.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import csv
from pathlib import Path
import random
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

Position = tuple[int, int]
SAFE, OBSTACLE, TARGET = 0, 1, 2


@dataclass(frozen=True)
class Config:
    size: int = 20
    max_energy: int = 160
    return_reserve: int = 8
    seed: int = 17
    obstacle_probability: float = 0.13
    target_probability: float = 0.10


@dataclass
class MissionResult:
    route: list[Position]
    discoveries: list[Position]
    final_position: Position
    energy_remaining: int
    returned_to_base: bool


def build_world(config: Config) -> tuple[list[list[int]], dict[Position, float]]:
    """Create deterministic synthetic terrain and illustrative science scores."""
    rng = random.Random(config.seed)
    world = [[SAFE for _ in range(config.size)] for _ in range(config.size)]
    science_value: dict[Position, float] = {}

    for y in range(config.size):
        for x in range(config.size):
            if (x, y) == (0, 0):
                continue
            roll = rng.random()
            if roll < config.obstacle_probability:
                world[y][x] = OBSTACLE
            elif roll < config.obstacle_probability + config.target_probability:
                world[y][x] = TARGET
                science_value[(x, y)] = round(rng.uniform(0.5, 2.0), 3)

    return world, science_value


def neighbors(world: list[list[int]], pos: Position) -> Iterable[Position]:
    size = len(world)
    x, y = pos
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < size and 0 <= ny < size and world[ny][nx] != OBSTACLE:
            yield (nx, ny)


def shortest_path(
    world: list[list[int]], start: Position, goal: Position
) -> list[Position] | None:
    """Return a shortest 4-connected path, including start and goal."""
    if start == goal:
        return [start]
    queue = deque([(start, [start])])
    seen = {start}

    while queue:
        pos, path = queue.popleft()
        for nxt in neighbors(world, pos):
            if nxt in seen:
                continue
            new_path = path + [nxt]
            if nxt == goal:
                return new_path
            seen.add(nxt)
            queue.append((nxt, new_path))
    return None


def choose_target(
    world: list[list[int]],
    science_value: dict[Position, float],
    position: Position,
    energy: int,
    start: Position,
    visited: set[Position],
    return_reserve: int,
) -> tuple[Position, list[Position]] | None:
    """Choose a reachable target only if outbound + return + reserve fit."""
    candidates: list[tuple[float, Position, list[Position]]] = []
    size = len(world)

    for y in range(size):
        for x in range(size):
            target = (x, y)
            if world[y][x] != TARGET or target in visited:
                continue

            outbound = shortest_path(world, position, target)
            home = shortest_path(world, target, start)
            if outbound is None or home is None:
                continue

            outbound_cost = len(outbound) - 1
            home_cost = len(home) - 1
            if energy < outbound_cost + home_cost + return_reserve:
                continue

            # Baseline heuristic, not a validated scientific information-gain model.
            score = science_value.get(target, 1.0) / max(1, outbound_cost)
            candidates.append((score, target, outbound))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1][1], item[1][0]))
    _, target, path = candidates[0]
    return target, path


def run_mission(config: Config) -> tuple[MissionResult, list[list[int]]]:
    world, science_value = build_world(config)
    start = (0, 0)
    position = start
    energy = config.max_energy
    visited = {start}
    route = [start]
    discoveries: list[Position] = []

    while True:
        choice = choose_target(
            world, science_value, position, energy, start,
            visited, config.return_reserve
        )
        if choice is None:
            break

        target, path = choice
        for step in path[1:]:
            if energy <= 0:
                break
            position = step
            energy -= 1
            route.append(position)
            visited.add(position)

            # Inspect any target crossed along the path exactly once.
            if world[position[1]][position[0]] == TARGET:
                discoveries.append(position)
                world[position[1]][position[0]] = SAFE
                science_value.pop(position, None)

        if energy <= 0:
            break

        home = shortest_path(world, position, start)
        if home is None or energy <= len(home) - 1 + config.return_reserve:
            break

        # A chosen target might have been inspected while traversing another path.
        if position != target and world[target[1]][target[0]] != TARGET:
            continue

    home = shortest_path(world, position, start)
    returned = False
    if home is not None and energy >= len(home) - 1:
        for step in home[1:]:
            position = step
            energy -= 1
            route.append(position)
        returned = position == start

    result = MissionResult(
        route=route,
        discoveries=discoveries,
        final_position=position,
        energy_remaining=energy,
        returned_to_base=returned,
    )
    return result, world


def write_outputs(
    config: Config, result: MissionResult, world: list[list[int]],
    output_dir: Path = Path("results")
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    route_file = output_dir / "mission_route.csv"
    with route_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "x", "y"])
        for step, (x, y) in enumerate(result.route):
            writer.writerow([step, x, y])

    cmap = ListedColormap(["#d9e8d1", "#303744", "#e5b64b"])
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.imshow(world, cmap=cmap, origin="lower", vmin=0, vmax=2)
    if result.route:
        ax.plot(
            [p[0] for p in result.route],
            [p[1] for p in result.route],
            color="blue", linewidth=1.5, label="Rover route"
        )
    ax.scatter(0, 0, color="green", s=100, label="Base")
    if result.discoveries:
        ax.scatter(
            [p[0] for p in result.discoveries],
            [p[1] for p in result.discoveries],
            color="red", marker="*", s=130, label="Inspected targets"
        )
    ax.set_title(f"APSE 2D Rover — synthetic map (seed={config.seed})")
    ax.set_xlabel("X grid coordinate")
    ax.set_ylabel("Y grid coordinate")
    ax.set_xticks(range(config.size))
    ax.set_yticks(range(config.size))
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "mission_map.png", dpi=150)
    plt.close(fig)


def main() -> None:
    config = Config()
    result, world = run_mission(config)
    write_outputs(config, result, world)
    print("APSE 2D Rover simulation finished (synthetic terrain).")
    print(f"Targets inspected: {len(result.discoveries)}")
    print(f"Steps travelled: {len(result.route) - 1}")
    print(f"Energy remaining: {result.energy_remaining}")
    print(f"Returned to base: {result.returned_to_base}")
    print("Outputs: results/mission_route.csv, results/mission_map.png")


if __name__ == "__main__":
    main()
