import argparse
import json

from asib.scenarios import run_fault_scenario


def main():
    parser = argparse.ArgumentParser(description="Run an ASIB digital-twin fault scenario")
    parser.add_argument(
        "scenario",
        choices=["thermal", "power", "network", "partition", "compute", "earth-loss", "robot-failure", "compound"],
        default="compound",
        nargs="?",
    )
    args = parser.parse_args()
    print(json.dumps(run_fault_scenario(args.scenario), indent=2))


if __name__ == "__main__":
    main()
