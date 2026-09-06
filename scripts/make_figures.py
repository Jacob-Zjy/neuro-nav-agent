from __future__ import annotations

import pandas as pd

from medevalops.config import FIGURES_DIR, RESULTS_DIR
from medevalops.figures import confusion_figure, performance_figure, priority_figure


def main() -> None:
    summary = pd.read_csv(RESULTS_DIR / "summary_metrics.csv")
    comparison = pd.read_csv(RESULTS_DIR / "paired_comparison.csv")
    predictions = pd.read_csv(RESULTS_DIR / "predictions.csv")
    priority = pd.read_csv(RESULTS_DIR / "data_priority.csv")
    quality = pd.read_csv(RESULTS_DIR / "data_quality.csv")
    outputs = []
    outputs.extend(performance_figure(summary, comparison, FIGURES_DIR))
    outputs.extend(confusion_figure(predictions, FIGURES_DIR))
    outputs.extend(priority_figure(priority, quality, FIGURES_DIR))
    print("\n".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()

