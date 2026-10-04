import argparse
import json

from asib.benchmark import run_compound_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(run_compound_benchmark(args.ticks), indent=2))


if __name__ == "__main__":
    main()
