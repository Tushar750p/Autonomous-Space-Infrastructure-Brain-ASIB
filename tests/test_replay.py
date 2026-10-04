import unittest

from asib.replay import StateReplay
from asib.runtime import ASIBRuntime


class TestReplay(unittest.TestCase):
    def test_runtime_builds_monotonic_replay(self):
        runtime = ASIBRuntime()
        runtime.run(3)
        self.assertEqual(len(runtime.replay.frames), 4)
        self.assertTrue(runtime.replay.validate())

    def test_replay_round_trips_json(self):
        runtime = ASIBRuntime()
        runtime.run(2)
        payload = runtime.replay.to_json()
        restored = StateReplay.from_json(payload)
        self.assertEqual(restored.export(), runtime.replay.export())
        self.assertTrue(restored.validate())

    def test_replay_detects_state_tampering(self):
        runtime = ASIBRuntime()
        runtime.run(2)
        payload = runtime.replay.export()
        payload[1]["state"]["earth_contact_available"] = False
        tampered = StateReplay.from_json(__import__("json").dumps(payload))
        self.assertFalse(tampered.validate())
        self.assertNotEqual(
            tampered.frames[1].digest,
            StateReplay._digest(
                tampered.frames[1].tick,
                tampered.frames[1].state,
                tampered.frames[1].previous_digest,
            ),
        )


if __name__ == "__main__":
    unittest.main()
