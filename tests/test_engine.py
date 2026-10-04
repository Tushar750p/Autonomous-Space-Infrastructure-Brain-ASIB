import unittest
from asib.engine import ASIBBrain
from asib.simulator import Simulator

class TestASIBBrain(unittest.TestCase):
    def test_thermal_recovery(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01")
        ASIBBrain().step(sim.world)
        node = sim.world.nodes["orbital-node-01"]
        self.assertLess(node.temperature_c, 85)
        self.assertEqual(node.status.value, "nominal")

    def test_power_reduction(self):
        sim = Simulator()
        sim.inject_power_failure("orbital-node-02")
        ASIBBrain().step(sim.world)
        self.assertLessEqual(sim.world.nodes["orbital-node-02"].workload, 45)

if __name__ == "__main__":
    unittest.main()
