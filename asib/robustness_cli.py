from __future__ import annotations

import argparse
import json

from .robustness import run_robustness_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic ASIB robustness trials")
    parser.add_argument("--ticks", type=int, default=10)
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261004)
    args = parser.parse_args()

    result = run_robustness_suite(args.ticks, args.trials, args.seed)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
