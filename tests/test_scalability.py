import unittest

from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestScalableSimulation(unittest.TestCase):
    def test_simulator_can_scale_without_changing_default(self):
        default = Simulator()
        scaled = Simulator(node_count=12)

        self.assertEqual(len(default.world.nodes), 3)
        self.assertEqual(len(scaled.world.nodes), 12)
        self.assertIn("orbital-node-12", scaled.world.nodes)
        self.assertEqual(len(scaled.world.links), 12 * 11)

    def test_scaled_runtime_completes_one_tick(self):
        runtime = ASIBRuntime(Simulator(node_count=10))
        report = runtime.tick()

        self.assertEqual(report.tick, 1)
        self.assertEqual(len(report.state), 10)
        self.assertTrue(runtime.world.audit_ledger.verify())


if __name__ == "__main__":
    unittest.main()
