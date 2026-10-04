import unittest

from asib.resources import migration_power_floor
from asib.simulator import Simulator


class TestEnergyReserve(unittest.TestCase):
    def test_normal_power_floor_is_25(self):
        sim = Simulator()
        sim.world.environment.phase_deg = 0
        self.assertEqual(migration_power_floor(sim.world), 25.0)

    def test_eclipse_power_floor_is_higher(self):
        sim = Simulator()
        sim.world.environment.phase_deg = 120
        self.assertEqual(migration_power_floor(sim.world), 35.0)

    def test_imminent_eclipse_raises_floor(self):
        sim = Simulator()
        sim.world.environment.phase_deg = 60
        self.assertEqual(migration_power_floor(sim.world), 30.0)


if __name__ == "__main__":
    unittest.main()
