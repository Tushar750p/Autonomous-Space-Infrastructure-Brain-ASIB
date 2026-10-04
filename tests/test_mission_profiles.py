import unittest

from asib.mission import MissionEvaluator, MissionProfile
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator


class TestMissionProfiles(unittest.TestCase):
    def test_weights_are_normalized(self):
        profile = MissionProfile(
            name="thermal-priority",
            availability_weight=1,
            thermal_weight=3,
            power_weight=1,
            critical_service_weight=0,
            network_weight=0,
            storage_weight=0,
        ).normalized()
        self.assertAlmostEqual(
            profile.availability_weight + profile.thermal_weight +
            profile.power_weight + profile.critical_service_weight +
            profile.network_weight,
            1.0,
        )

    def test_custom_profile_changes_score(self):
        sim = Simulator()
        default_score = MissionEvaluator().evaluate(sim.world)["score"]
        thermal_only = MissionEvaluator(
            MissionProfile(
                name="thermal-only",
                availability_weight=0,
                thermal_weight=1,
                power_weight=0,
                critical_service_weight=0,
                network_weight=0,
                storage_weight=1,
            )
        ).evaluate(sim.world)

        self.assertEqual(thermal_only["profile"], "thermal-only")
        self.assertIn("storage_health_pct", thermal_only)
        self.assertNotEqual(thermal_only["score"], default_score)

    def test_runtime_passes_profile_into_brain(self):
        runtime = ASIBRuntime(
            mission_profile=MissionProfile(
                name="thermal-priority",
                availability_weight=0,
                thermal_weight=1,
                power_weight=0,
                critical_service_weight=0,
                network_weight=0,
            )
        )
        decision_before = runtime.brain.mission.profile.name
        self.assertEqual(decision_before, "thermal-priority")


if __name__ == "__main__":
    unittest.main()
