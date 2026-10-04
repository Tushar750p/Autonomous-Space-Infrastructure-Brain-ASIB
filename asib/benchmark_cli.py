import argparse
import json

from .benchmark import run_compound_benchmark


def main():
    parser = argparse.ArgumentParser(description="Run the ASIB compound benchmark")
    parser.add_argument("--ticks", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(run_compound_benchmark(args.ticks), indent=2))
