import unittest

from asib.planner import MultiNodePlanner
from asib.resources import ResourceReservationBook
from asib.simulator import Simulator


class TestResourceReservations(unittest.TestCase):
    def test_reservation_cannot_exceed_free_cpu(self):
        sim = Simulator()
        target = sim.world.nodes["orbital-node-03"]
        book = ResourceReservationBook.create()

        self.assertTrue(book.reserve_cpu(target.node_id, target, 50))
        self.assertFalse(book.reserve_cpu(target.node_id, target, 31))
        self.assertEqual(book.available_cpu(target.node_id, target), 30)

    def test_multi_source_plan_respects_target_capacity(self):
        sim = Simulator()
        sim.inject_thermal_failure("orbital-node-01", 92)
        sim.inject_power_failure("orbital-node-02", 20)
        planner = MultiNodePlanner()

        plan = planner.plan(sim.world)
        migrations = [a for a in plan.actions if a.action_type == "migrate"]
        target_load = sum(a.amount for a in migrations if a.target_node == "orbital-node-03")

        self.assertLessEqual(target_load, sim.world.nodes["orbital-node-03"].free_cpu)
        self.assertLessEqual(target_load, sim.world.nodes["orbital-node-03"].free_cpu)

        reservation = ResourceReservationBook.create()
        for action in migrations:
            if action.target_node:
                self.assertTrue(
                    reservation.reserve_cpu(
                        action.target_node,
                        sim.world.nodes[action.target_node],
                        action.amount,
                    )
                )


if __name__ == "__main__":
    unittest.main()
