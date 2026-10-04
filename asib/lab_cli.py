from __future__ import annotations

import argparse
import json

from .lab import run_research_lab


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete ASIB local research validation lab")
    parser.add_argument("--ticks", type=int, default=5)
    parser.add_argument("--robustness-trials", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261004)
    args = parser.parse_args()

    print(json.dumps(
        run_research_lab(args.ticks, args.robustness_trials, args.seed),
        indent=2,
        default=str,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
