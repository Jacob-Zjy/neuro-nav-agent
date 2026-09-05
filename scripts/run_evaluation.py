from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from neuronav.benchmark import load_benchmark
from neuronav.evaluation import evaluate_all
from neuronav.io import load_trials


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", default="data/processed/trials_snapshot.csv")
    parser.add_argument("--benchmark", default="data/benchmark/cases.jsonl")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    metrics, predictions = evaluate_all(load_benchmark(args.benchmark), load_trials(args.trials))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(row) for row in metrics]).to_csv(output / "benchmark_metrics.csv", index=False)
    pd.DataFrame(predictions).to_csv(output / "benchmark_predictions.csv", index=False)
    print(pd.DataFrame([asdict(row) for row in metrics]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

