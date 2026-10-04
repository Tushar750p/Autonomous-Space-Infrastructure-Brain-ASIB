import os
import tempfile
import unittest

from asib.config import ASIBConfig
from asib.runtime import ASIBRuntime
from asib.simulator import Simulator
from asib.storage import EventStore


class TestStorage(unittest.TestCase):
    def test_event_store_persists_events_and_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "asib.db")
            store = EventStore(path)

            sim = Simulator()
            runtime = ASIBRuntime(sim)
            runtime.store = store
            sim.inject_thermal_failure("orbital-node-01", 96)
            runtime.tick()

            counts = store.counts()
            self.assertGreater(counts["events"], 0)
            self.assertEqual(counts["decisions"], 1)

            store.close()

    def test_runtime_storage_is_disabled_by_default(self):
        os.environ.pop("ASIB_STORE_PATH", None)
        runtime = ASIBRuntime()
        try:
            self.assertIsNone(runtime.store)
            self.assertEqual(runtime.storage_status()["enabled"], False)
        finally:
            runtime.reset()


if __name__ == "__main__":
    unittest.main()
