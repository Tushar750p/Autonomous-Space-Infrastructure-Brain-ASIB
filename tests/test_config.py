import os
import unittest

from asib.config import ASIBConfig


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        for key in ("ASIB_HOST", "ASIB_PORT", "ASIB_TICK_INTERVAL_S"):
            os.environ.pop(key, None)

        config = ASIBConfig.from_env()
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.tick_interval_s, 1.0)

    def test_environment_overrides_are_clamped(self):
        os.environ["ASIB_HOST"] = "127.0.0.1"
        os.environ["ASIB_PORT"] = "99999"
        os.environ["ASIB_TICK_INTERVAL_S"] = "0.001"
        try:
            config = ASIBConfig.from_env()
            self.assertEqual(config.host, "127.0.0.1")
            self.assertEqual(config.port, 65535)
            self.assertEqual(config.tick_interval_s, 0.05)
        finally:
            for key in ("ASIB_HOST", "ASIB_PORT", "ASIB_TICK_INTERVAL_S"):
                os.environ.pop(key, None)


if __name__ == "__main__":
    unittest.main()
