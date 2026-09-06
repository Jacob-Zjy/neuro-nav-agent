from __future__ import annotations

import json

import pandas as pd
import pytest

from medevalops.metrics import (
    _benjamini_hochberg,
    _classification_arrays,
    evaluate_predictions,
    expected_calibration_error,
    paired_comparison,
)


def make_predictions() -> pd.DataFrame:
    rows = []
    for task in ["KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR"]:
        for index, target in enumerate(["A", "B", "A", "B"]):
            for strategy in ["direct", "rubric"]:
                prediction = target
                if strategy == "direct" and index == 0:
                    prediction = "B" if target == "A" else "A"
                probability = {"A": 0.8 if prediction == "A" else 0.2, "B": 0.8 if prediction == "B" else 0.2}
                rows.append(
                    {
                        "item_id": f"{task}:{index}",
                        "task": task,
                        "strategy": strategy,
                        "target": target,
                        "prediction": prediction,
                        "correct": prediction == target,
                        "confidence": 0.8,
                        "margin": 0.6,
                        "entropy": 0.5,
                        "normalized_entropy": 0.4,
                        "choice_count": 2,
                        "choice_probabilities": json.dumps(probability),
                    }
                )
    return pd.DataFrame(rows)


def test_ece_known_value() -> None:
    value = expected_calibration_error(
        correct=pd.Series([1.0, 1.0, 0.0]).to_numpy(),
        confidence=pd.Series([0.8, 0.8, 0.8]).to_numpy(),
        bins=10,
    )
    assert value == pytest.approx(abs(2 / 3 - 0.8))


def test_paired_comparison_uses_all_three_tasks() -> None:
    result = paired_comparison(make_predictions(), bootstrap_draws=100, seed=4)
    assert len(result) == 3
    assert result["accuracy_delta"].eq(0.25).all()
    assert result["discordant"].eq(1).all()
    assert result["mcnemar_bh_p"].between(0, 1).all()


def test_bh_adjustment_is_monotone_in_example() -> None:
    adjusted = _benjamini_hochberg([0.01, 0.04, 0.20])
    assert adjusted == pytest.approx([0.03, 0.06, 0.20])


def test_overall_metrics_keep_task_label_spaces_separate() -> None:
    direct = make_predictions().query("strategy == 'direct'")
    truth, prediction = _classification_arrays(direct)
    assert len(set(truth)) == 6
    assert all("::" in label for label in truth)
    summary = evaluate_predictions(make_predictions(), bootstrap_draws=20, seed=5)
    assert len(summary) == 8
    assert summary[["accuracy_ci_low", "accuracy_ci_high"]].notna().all().all()
