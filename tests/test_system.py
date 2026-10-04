import unittest

from asib.benchmark import run_compound_benchmark
from asib.comms import CommunicationModel
from asib.models import World
from asib.network import NetworkModel
from asib.robotics import RobotFleet
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestASIBSystem(unittest.TestCase):
    def test_closed_loop_runtime_advances_and_records_telemetry(self):
        runtime = ASIBRuntime()
        first = runtime.tick()
        self.assertEqual(first.tick, 1)
        self.assertEqual(runtime.world.tick, 1)
        self.assertEqual(len(runtime.world.telemetry["orbital-node-01"]), 1)

    def test_telemetry_accumulates_for_prediction(self):
        runtime = ASIBRuntime()
        for _ in range(4):
            runtime.tick()
        history = runtime.world.telemetry["orbital-node-01"]
        self.assertGreaterEqual(len(history), 4)

    def test_delayed_message_delivery(self):
        sim = Simulator()
        sim.inject_comms_delay(3)
        comms = CommunicationModel()
        message = comms.send(sim.world, "orbital-node-01", "orbital-node-02", "health")
        self.assertIsNone(comms.deliver(sim.world, message))
        sim.world.tick = 3
        event = comms.deliver(sim.world, message)
        self.assertIsNotNone(event)

    def test_network_partition_blocks_migration_target(self):
        sim = Simulator()
        network = NetworkModel()
        network.partition_node(sim.world, "orbital-node-02")
        self.assertFalse(network.is_connected(sim.world, "orbital-node-02", "orbital-node-01"))

    def test_robot_service_simulation(self):
        sim = Simulator()
        sim.world.nodes["orbital-node-01"].temperature_c = 90
        fleet = RobotFleet(sim.world)
        fleet.enqueue("orbital-node-01", "inspect-and-service", priority=10)
        fleet.dispatch()
        fleet.step()
        fleet.step()
        self.assertLess(sim.world.nodes["orbital-node-01"].temperature_c, 90)

    def test_decision_trace_is_recorded(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 96)
        ASIBRuntime(sim).brain.step(sim.world)
        self.assertTrue(sim.world.decision_log)
        self.assertIn("trace_id", sim.world.decision_log[-1])

    def test_compound_benchmark_returns_bounded_score(self):
        result = run_compound_benchmark(5)
        self.assertGreaterEqual(result["final_mission"]["score"], 0)
        self.assertLessEqual(result["final_mission"]["score"], 100)
        self.assertIn("robot_states", result)


if __name__ == "__main__":
    unittest.main()
