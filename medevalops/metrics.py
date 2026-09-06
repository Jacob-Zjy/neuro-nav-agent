from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score

from .config import RESULTS_DIR, SEED, STRATEGIES, TASKS


def expected_calibration_error(
    correct: np.ndarray, confidence: np.ndarray, bins: int = 10
) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    value = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        include = (confidence > lower) & (confidence <= upper)
        if lower == 0.0:
            include |= confidence == 0.0
        if include.any():
            value += float(include.mean()) * abs(
                float(correct[include].mean()) - float(confidence[include].mean())
            )
    return value


def multiclass_brier(group: pd.DataFrame) -> float:
    values: list[float] = []
    for row in group.itertuples(index=False):
        probabilities = json.loads(row.choice_probabilities)
        values.append(
            sum(
                (float(probability) - (1.0 if label == row.target else 0.0)) ** 2
                for label, probability in probabilities.items()
            )
        )
    return float(np.mean(values))


def _classification_arrays(group: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if group["task"].nunique() > 1:
        truth = (group["task"].astype(str) + "::" + group["target"].astype(str)).to_numpy()
        prediction = (
            group["task"].astype(str) + "::" + group["prediction"].astype(str)
        ).to_numpy()
        return truth, prediction
    return group["target"].to_numpy(), group["prediction"].to_numpy()


def metric_row(group: pd.DataFrame) -> dict[str, float | int]:
    truth, prediction = _classification_arrays(group)
    labels = sorted(set(truth) | set(prediction))
    target_labels = sorted(set(truth))
    correct = group["correct"].astype(float).to_numpy()
    confidence = group["confidence"].astype(float).to_numpy()
    recalls = [
        float(np.mean(prediction[truth == label] == label)) for label in target_labels
    ]
    return {
        "n": len(group),
        "accuracy": float(accuracy_score(truth, prediction)),
        "macro_f1": float(
            f1_score(truth, prediction, labels=labels, average="macro", zero_division=0)
        ),
        "balanced_accuracy": float(np.mean(recalls)),
        "ece_10": expected_calibration_error(correct, confidence, bins=10),
        "brier_multiclass": multiclass_brier(group),
        "mean_confidence": float(confidence.mean()),
        "mean_margin": float(group["margin"].mean()),
    }


def _bootstrap_interval(
    group: pd.DataFrame,
    metric: str,
    *,
    draws: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    truth, prediction = _classification_arrays(group)
    labels = sorted(set(truth) | set(prediction))
    n = len(group)
    values = np.empty(draws, dtype=float)
    for draw in range(draws):
        if group["task"].nunique() > 1:
            sampled = []
            for task in sorted(group["task"].unique()):
                task_indices = np.flatnonzero(group["task"].to_numpy() == task)
                sampled.append(rng.choice(task_indices, size=len(task_indices), replace=True))
            indices = np.concatenate(sampled)
        else:
            indices = rng.integers(0, n, size=n)
        if metric == "accuracy":
            values[draw] = np.mean(truth[indices] == prediction[indices])
        elif metric == "macro_f1":
            values[draw] = f1_score(
                truth[indices],
                prediction[indices],
                labels=labels,
                average="macro",
                zero_division=0,
            )
        else:
            raise ValueError(metric)
    return tuple(float(value) for value in np.quantile(values, [0.025, 0.975]))


def evaluate_predictions(
    predictions: pd.DataFrame,
    *,
    bootstrap_draws: int = 2000,
    seed: int = SEED,
) -> pd.DataFrame:
    required = {
        "item_id",
        "task",
        "strategy",
        "target",
        "prediction",
        "correct",
        "confidence",
        "choice_probabilities",
    }
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Predictions missing columns: {sorted(missing)}")
    if predictions.duplicated(["item_id", "strategy"]).any():
        raise ValueError("Duplicate item_id/strategy rows")

    rows: list[dict[str, object]] = []
    groups = [(task, strategy) for task in TASKS for strategy in STRATEGIES]
    groups += [("Overall", strategy) for strategy in STRATEGIES]
    for index, (task, strategy) in enumerate(groups):
        group = predictions[predictions["strategy"].eq(strategy)]
        if task != "Overall":
            group = group[group["task"].eq(task)]
        summary = metric_row(group)
        for metric in ("accuracy", "macro_f1"):
            lower, upper = _bootstrap_interval(
                group,
                metric,
                draws=bootstrap_draws,
                seed=seed + index * 17 + (0 if metric == "accuracy" else 1),
            )
            summary[f"{metric}_ci_low"] = lower
            summary[f"{metric}_ci_high"] = upper
        rows.append({"task": task, "strategy": strategy, **summary})
    return pd.DataFrame(rows)


def _paired_bootstrap_delta(
    paired: pd.DataFrame, *, draws: int, seed: int
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    direct = paired["direct"].astype(float).to_numpy()
    rubric = paired["rubric"].astype(float).to_numpy()
    n = len(paired)
    values = np.empty(draws, dtype=float)
    for draw in range(draws):
        indices = rng.integers(0, n, size=n)
        values[draw] = float(np.mean(rubric[indices] - direct[indices]))
    return tuple(float(value) for value in np.quantile(values, [0.025, 0.975]))


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 1.0
    total = len(values)
    for reverse_rank, index in enumerate(order[::-1], start=1):
        rank = total - reverse_rank + 1
        running = min(running, values[index] * total / rank)
        adjusted[index] = min(running, 1.0)
    return adjusted.tolist()


def paired_comparison(
    predictions: pd.DataFrame,
    *,
    bootstrap_draws: int = 2000,
    seed: int = SEED,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index, task in enumerate(TASKS):
        subset = predictions[predictions["task"].eq(task)]
        pivot = subset.pivot(index="item_id", columns="strategy", values="correct")
        if set(pivot.columns) != set(STRATEGIES) or pivot.isna().any().any():
            raise ValueError(f"Incomplete paired predictions for {task}")
        pivot = pivot.astype(bool)
        direct_only = int((pivot["direct"] & ~pivot["rubric"]).sum())
        rubric_only = int((~pivot["direct"] & pivot["rubric"]).sum())
        discordant = direct_only + rubric_only
        p_value = (
            float(binomtest(min(direct_only, rubric_only), discordant, 0.5).pvalue)
            if discordant
            else 1.0
        )
        delta = float(pivot["rubric"].mean() - pivot["direct"].mean())
        lower, upper = _paired_bootstrap_delta(
            pivot, draws=bootstrap_draws, seed=seed + index * 101
        )
        rows.append(
            {
                "task": task,
                "n": len(pivot),
                "accuracy_direct": float(pivot["direct"].mean()),
                "accuracy_rubric": float(pivot["rubric"].mean()),
                "accuracy_delta": delta,
                "delta_ci_low": lower,
                "delta_ci_high": upper,
                "direct_only_correct": direct_only,
                "rubric_only_correct": rubric_only,
                "discordant": discordant,
                "mcnemar_exact_p": p_value,
            }
        )
    result = pd.DataFrame(rows)
    result["mcnemar_bh_p"] = _benjamini_hochberg(result["mcnemar_exact_p"].tolist())
    return result


def confusion_long(predictions: pd.DataFrame) -> pd.DataFrame:
    counts = (
        predictions.groupby(["task", "strategy", "target", "prediction"], observed=True)
        .size()
        .rename("n")
        .reset_index()
    )
    totals = counts.groupby(["task", "strategy", "target"], observed=True)["n"].transform("sum")
    counts["row_fraction"] = counts["n"] / totals
    return counts


def write_metric_outputs(
    summary: pd.DataFrame,
    comparison: pd.DataFrame,
    confusion: pd.DataFrame,
    results_dir: Path = RESULTS_DIR,
) -> tuple[Path, Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        results_dir / "summary_metrics.csv",
        results_dir / "paired_comparison.csv",
        results_dir / "confusion_long.csv",
    )
    summary.to_csv(paths[0], index=False)
    comparison.to_csv(paths[1], index=False)
    confusion.to_csv(paths[2], index=False)
    return paths
