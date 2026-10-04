import unittest

from asib.benchmark import run_compound_benchmark
from asib.comms import CommunicationModel
from asib.models import World
from asib.robotics import RobotFleet
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestASIBSystem(unittest.TestCase):
    def test_closed_loop_runtime_advances(self):
        runtime = ASIBRuntime()
        first = runtime.tick()
        self.assertEqual(first.tick, 1)
        self.assertEqual(runtime.world.tick, 1)

    def test_delayed_message_delivery(self):
        sim = Simulator()
        sim.inject_comms_delay(3)
        comms = CommunicationModel()
        message = comms.send(sim.world, "orbital-node-01", "orbital-node-02", "health")
        self.assertIsNone(comms.deliver(sim.world, message))
        sim.world.tick = 3
        event = comms.deliver(sim.world, message)
        self.assertIsNotNone(event)

    def test_robot_service_simulation(self):
        sim = Simulator()
        sim.world.nodes["orbital-node-01"].temperature_c = 90
        fleet = RobotFleet(sim.world)
        fleet.enqueue("orbital-node-01", "inspect-and-service", priority=10)
        fleet.dispatch()
        fleet.step()
        fleet.step()
        self.assertLess(sim.world.nodes["orbital-node-01"].temperature_c, 90)

    def test_compound_benchmark_returns_bounded_score(self):
        result = run_compound_benchmark(5)
        self.assertGreaterEqual(result["final_mission"]["score"], 0)
        self.assertLessEqual(result["final_mission"]["score"], 100)


if __name__ == "__main__":
    unittest.main()
