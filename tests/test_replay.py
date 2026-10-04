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


if __name__ == "__main__":
    unittest.main()
