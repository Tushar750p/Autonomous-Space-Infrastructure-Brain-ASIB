import argparse
import json

from asib.experiments import run_experiment_suite


def main():
    parser = argparse.ArgumentParser(description="Run the reproducible ASIB experiment suite")
    parser.add_argument("--ticks", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(run_experiment_suite(args.ticks), indent=2))


if __name__ == "__main__":
    main()
