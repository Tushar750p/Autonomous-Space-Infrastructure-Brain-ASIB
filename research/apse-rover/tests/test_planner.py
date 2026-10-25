from app import Config, OBSTACLE, TARGET, choose_target, run_mission, shortest_path


def test_shortest_path_avoids_obstacle():
    world = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    path = shortest_path(world, (0, 0), (2, 0))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)
    assert all(world[y][x] != OBSTACLE for x, y in path)


def test_unreachable_target_returns_none():
    world = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ]
    assert shortest_path(world, (0, 0), (2, 2)) is None


def test_target_rejected_if_return_budget_does_not_fit():
    world = [
        [0, 0, 0],
        [0, 0, 2],
        [0, 0, 0],
    ]
    target = (2, 1)
    choice = choose_target(
        world=world,
        science_value={target: 1.0},
        position=(0, 0),
        energy=3,
        start=(0, 0),
        visited={(0, 0)},
        return_reserve=2,
    )
    assert choice is None


def test_mission_is_deterministic_and_returns_when_possible():
    config = Config(size=10, max_energy=100, return_reserve=5, seed=4)
    first, _ = run_mission(config)
    second, _ = run_mission(config)
    assert first.route == second.route
    assert first.discoveries == second.discoveries
    assert first.returned_to_base
    assert first.final_position == (0, 0)


def test_generated_world_has_only_valid_cell_types():
    _, world = run_mission(Config(size=8, max_energy=40, seed=9))
    assert all(cell in (0, 1, 2) for row in world for cell in row)
