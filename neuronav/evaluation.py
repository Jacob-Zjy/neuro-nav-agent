from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .benchmark import BenchmarkCase
from .eligibility import RECRUITING_STATUSES, assess_structured
from .models import TrialRecord
from .normalization import condition_similarity, normalize_sex


@dataclass(frozen=True)
class MetricRow:
    method: str
    n: int
    accuracy: float
    balanced_accuracy: float
    ci_low: float
    ci_high: float
    precision: float
    recall: float
    specificity: float
    f1: float
    false_positive_rate: float
    false_negative_rate: float


def predict(case: BenchmarkCase, trial: TrialRecord, method: str) -> bool:
    profile = case.profile
    condition_ok = condition_similarity(profile.condition, trial.conditions) >= 0.34
    if method == "Keyword retrieval":
        return condition_ok
    status_ok = trial.overall_status in RECRUITING_STATUSES
    age_ok = (
        profile.age is not None
        and (trial.minimum_age_years is None or profile.age >= trial.minimum_age_years)
        and (trial.maximum_age_years is None or profile.age <= trial.maximum_age_years)
    )
    if method == "Structured filters":
        return condition_ok and status_ok and age_ok
    if method == "NeuroNav-Agent":
        decision = assess_structured(profile, trial)
        return decision.status == "potential_match" and decision.components["location"] == 1.0
    raise ValueError(f"Unknown method: {method}")


def _confusion(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    return tp, tn, fp, fn


def _balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp, tn, fp, fn = _confusion(y_true, y_pred)
    recall = tp / (tp + fn) if tp + fn else np.nan
    specificity = tn / (tn + fp) if tn + fp else np.nan
    return float(np.nanmean([recall, specificity]))


def evaluate_method(
    method: str,
    cases: list[BenchmarkCase],
    trials_by_id: dict[str, TrialRecord],
    bootstrap_samples: int = 2000,
    seed: int = 42,
) -> tuple[MetricRow, list[dict[str, object]]]:
    records = []
    for case in cases:
        trial = trials_by_id[case.trial_nct_id]
        prediction = predict(case, trial, method)
        records.append({
            "case_id": case.case_id,
            "trial_nct_id": case.trial_nct_id,
            "perturbation": case.perturbation,
            "expected_match": case.expected_match,
            "predicted_match": prediction,
            "correct": prediction == case.expected_match,
        })
    y_true = np.array([int(row["expected_match"]) for row in records])
    y_pred = np.array([int(row["predicted_match"]) for row in records])
    tp, tn, fp, fn = _confusion(y_true, y_pred)
    accuracy = (tp + tn) / len(y_true)
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    rng = np.random.default_rng(seed)
    bootstrap = []
    for _ in range(bootstrap_samples):
        indices = rng.integers(0, len(y_true), len(y_true))
        bootstrap.append(_balanced_accuracy(y_true[indices], y_pred[indices]))
    ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975])
    row = MetricRow(
        method=method,
        n=len(y_true),
        accuracy=accuracy,
        balanced_accuracy=_balanced_accuracy(y_true, y_pred),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        precision=precision,
        recall=recall,
        specificity=specificity,
        f1=f1,
        false_positive_rate=fp / (fp + tn) if fp + tn else 0.0,
        false_negative_rate=fn / (fn + tp) if fn + tp else 0.0,
    )
    return row, records


def evaluate_all(
    cases: list[BenchmarkCase], trials: list[TrialRecord]
) -> tuple[list[MetricRow], list[dict[str, object]]]:
    trials_by_id = {trial.nct_id: trial for trial in trials}
    metrics = []
    predictions = []
    for method in ("Keyword retrieval", "Structured filters", "NeuroNav-Agent"):
        row, records = evaluate_method(method, cases, trials_by_id)
        metrics.append(row)
        for record in records:
            predictions.append({"method": method, **record})
    return metrics, predictions
