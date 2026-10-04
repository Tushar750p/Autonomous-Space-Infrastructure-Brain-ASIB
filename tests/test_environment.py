import unittest

from asib.environment import OrbitalEnvironment
from asib.simulator import Simulator


class TestOrbitalEnvironment(unittest.TestCase):
    def test_environment_cycles_between_sunlight_and_eclipse(self):
        env = OrbitalEnvironment()
        self.assertFalse(env.in_eclipse)
        env.advance()
        self.assertFalse(env.in_eclipse)
        env.advance()
        self.assertTrue(env.in_eclipse)

    def test_eclipse_reduces_generation_and_raises_thermal_bias(self):
        env = OrbitalEnvironment()
        sun_generation = env.solar_generation_pct
        sun_bias = env.cooling_bias_c

        for _ in range(3):
            env.advance()

        self.assertTrue(env.in_eclipse)
        self.assertLess(env.solar_generation_pct, sun_generation)
        self.assertGreater(env.cooling_bias_c, sun_bias)

    def test_simulator_exposes_environment_without_breaking_node_snapshot(self):
        sim = Simulator()
        snapshot = sim.snapshot()
        self.assertEqual(set(snapshot), set(sim.world.nodes))
        self.assertEqual(len(snapshot), 3)

        sim.advance_physics()
        self.assertEqual(sim.environment_snapshot()["phase_deg"], 30.0)


if __name__ == "__main__":
    unittest.main()
