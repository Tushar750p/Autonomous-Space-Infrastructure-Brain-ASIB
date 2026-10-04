import unittest

from asib.selftest import run_selftest


class TestSelfTest(unittest.TestCase):
    def test_integrated_selftest_passes(self):
        result = run_selftest(2)
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
