import unittest

from asib.checkpoint import export_world, restore_world
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestCheckpoint(unittest.TestCase):
    def test_checkpoint_round_trip_preserves_operational_state(self):
        runtime = ASIBRuntime()
        runtime.simulator.inject_thermal_failure("orbital-node-01", 96)
        runtime.tick()
        runtime.tick()

        restored = restore_world(export_world(runtime.world))

        self.assertEqual(restored.tick, runtime.world.tick)
        self.assertEqual(restored.nodes.keys(), runtime.world.nodes.keys())
        self.assertEqual(
            restored.nodes["orbital-node-01"].temperature_c,
            runtime.world.nodes["orbital-node-01"].temperature_c,
        )
        self.assertEqual(
            len(restored.telemetry["orbital-node-01"]),
            len(runtime.world.telemetry["orbital-node-01"]),
        )
        self.assertEqual(restored.decision_log, runtime.world.decision_log)
        self.assertTrue(restored.audit_ledger.verify())

    def test_checkpoint_restores_custom_orbital_parameters(self):
        sim = Simulator()
        sim.world.environment.angular_rate_deg_per_tick = 12.5
        sim.world.environment.phase_deg = 144.0

        restored = restore_world(export_world(sim.world))

        self.assertEqual(restored.environment.phase_deg, 144.0)
        self.assertEqual(restored.environment.angular_rate_deg_per_tick, 12.5)


if __name__ == "__main__":
    unittest.main()
