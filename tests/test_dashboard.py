import json
import threading
import unittest
import urllib.error
import urllib.request

from http.server import ThreadingHTTPServer

from asib.dashboard import DashboardHandler


class TestDashboardAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        DashboardHandler.runtime.reset()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def fetch_json(self, path):
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return response.status, json.loads(response.read().decode())

    def test_health_and_export_endpoints(self):
        status, health = self.fetch_json("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["audit_chain"])
        self.assertTrue(health["replay_journal"])
        self.assertIn("decision_class", health)
        self.assertIn("needs_human_review", health)

        status, calibration = self.fetch_json("/api/calibration")
        self.assertEqual(status, 200)
        self.assertIn("summary", calibration)

        status, replay = self.fetch_json("/api/replay")
        self.assertEqual(status, 200)
        self.assertEqual(replay[0]["tick"], 0)

        status, checkpoint = self.fetch_json("/api/checkpoint")
        self.assertEqual(status, 200)
        self.assertEqual(checkpoint["format_version"], 1)

        status, storage = self.fetch_json("/api/storage")
        self.assertEqual(status, 200)
        self.assertIn("enabled", storage)

    def test_tick_and_eclipse_scenario(self):
        status, tick = self.fetch_json("/api/tick")
        self.assertEqual(status, 200)
        self.assertEqual(tick["tick"], 1)
        self.assertIn("resources", tick)
        self.assertIn("forecast_calibration", tick)

        status, scenario = self.fetch_json("/api/scenario?name=eclipse")
        self.assertEqual(status, 200)
        self.assertTrue(scenario["environment"]["in_eclipse"])

        status, state = self.fetch_json("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(state["environment"]["phase_deg"], 150.0)
        self.assertIn("health", state)
        self.assertIn("needs_human_review", state["health"])

        status, robustness = self.fetch_json("/api/robustness?ticks=1&trials=1")
        self.assertEqual(status, 200)
        self.assertTrue(robustness["deterministic"])
        self.assertEqual(len(robustness["scenarios"]), 9)

    def test_invalid_query_values_return_400(self):
        for path, message in (
            ("/api/robustness?ticks=abc&trials=1", "ticks must be an integer"),
            ("/api/robustness?ticks=101&trials=1", "ticks must be in [1, 100]"),
            ("/api/experiments?ticks=0", "ticks must be in [1, 500]"),
        ):
            with self.subTest(path=path):
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    self.fetch_json(path)
                self.assertEqual(ctx.exception.code, 400)
                body = ctx.exception.read().decode()
                self.assertIn(message, body)


if __name__ == "__main__":
    unittest.main()
