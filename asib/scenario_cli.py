from __future__ import annotations

import argparse
import json

from .scenarios import run_fault_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic ASIB research scenario")
    parser.add_argument(
        "scenario",
        choices=(
            "thermal",
            "power",
            "compute",
            "network",
            "partition",
            "earth-loss",
            "eclipse",
            "eclipse-compound",
            "robot-failure",
            "compound",
        ),
    )
    args = parser.parse_args()
    print(json.dumps(run_fault_scenario(args.scenario), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
