from __future__ import annotations

import json

import pandas as pd

from medevalops.data import EvalItem
from medevalops.prompts import messages, system_prompt
from medevalops.strategy import build_data_priority


def test_rubric_prompt_contains_task_rule_without_target() -> None:
    item = EvalItem("x", "x", "KUAKE-QQR", "问题", "完全一致", ("完全一致", "无关"))
    prompt = system_prompt(item, "rubric")
    assert "查询2相对查询1" in prompt
    assert messages(item, "rubric")[-1]["content"] == "问题"


def test_unknown_strategy_rejected() -> None:
    item = EvalItem("x", "x", "KUAKE-QIC", "问题", "A", ("A", "B"))
    try:
        system_prompt(item, "unknown")
    except ValueError as exc:
        assert "Unknown prompt strategy" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_priority_flags_high_confidence_error() -> None:
    rows = []
    for strategy, prediction, correct, confidence in [
        ("direct", "B", False, 0.7),
        ("rubric", "B", False, 0.9),
    ]:
        rows.append(
            {
                "item_id": "x",
                "task": "KUAKE-QIC",
                "target": "A",
                "strategy": strategy,
                "prediction": prediction,
                "correct": correct,
                "confidence": confidence,
                "normalized_entropy": 0.2,
                "choice_probabilities": json.dumps({"A": 0.1, "B": 0.9}),
            }
        )
    result = build_data_priority(pd.DataFrame(rows))
    assert result.iloc[0]["high_confidence_error_rate"] == 1.0
    assert "复核标签规范" in result.iloc[0]["recommended_action"]

