from __future__ import annotations

import argparse

import pandas as pd

from medevalops.config import RESULTS_DIR, SEED
from medevalops.metrics import (
    confusion_long,
    evaluate_predictions,
    paired_comparison,
    write_metric_outputs,
)
from medevalops.strategy import build_data_priority, write_priority


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate predictions and derive data priorities.")
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    prediction_path = RESULTS_DIR / "predictions.csv"
    if not prediction_path.exists():
        raise SystemExit("Missing predictions. Run: python -m scripts.run_inference")
    predictions = pd.read_csv(prediction_path)
    summary = evaluate_predictions(
        predictions, bootstrap_draws=args.bootstrap_draws, seed=args.seed
    )
    comparison = paired_comparison(
        predictions, bootstrap_draws=args.bootstrap_draws, seed=args.seed
    )
    confusion = confusion_long(predictions)
    metric_paths = write_metric_outputs(summary, comparison, confusion)
    priority_path = write_priority(build_data_priority(predictions))
    print(f"Metrics: {', '.join(str(path) for path in metric_paths)}")
    print(f"Data priority: {priority_path}")


if __name__ == "__main__":
    main()

