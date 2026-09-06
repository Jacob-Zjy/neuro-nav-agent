from __future__ import annotations

import numpy as np
import pandas as pd

from medevalops.audit import audit_items
from medevalops.data import (
    EvalItem,
    _as_choices,
    build_items,
    canonicalize_label,
    normalized_text,
    write_public_index,
)


def test_choices_accept_parquet_numpy_array() -> None:
    choices = np.array(["相关", "不相关"], dtype=object)
    assert _as_choices(choices) == ("相关", "不相关")


def test_qic_label_alias_uses_promptcblue_evaluator_vocabulary() -> None:
    assert canonicalize_label("KUAKE-QIC", "疾病表述") == "疾病描述"
    assert canonicalize_label("KUAKE-QQR", "疾病表述") == "疾病表述"


def test_qic_adds_promptcblue_implicit_reject_option() -> None:
    frame = pd.DataFrame(
        [{
            "input": "测试问题",
            "target": "非上述类型",
            "answer_choices": np.array(["治疗方案", "病情诊断"], dtype=object),
            "task_dataset": "KUAKE-QIC",
            "sample_id": "dev-x",
        }]
    )
    # Isolate the row-level rule without invoking the full-dataset count guard.
    from medevalops import data as data_module

    original_tasks = data_module.TASKS
    original_counts = data_module.EXPECTED_TASK_ROWS
    try:
        data_module.TASKS = ("KUAKE-QIC",)
        data_module.EXPECTED_TASK_ROWS = {"KUAKE-QIC": 1}
        item = build_items(frame)[0]
    finally:
        data_module.TASKS = original_tasks
        data_module.EXPECTED_TASK_ROWS = original_counts
    assert item.choices[-1] == "非上述类型"
    assert item.target in item.choices


def sample_items() -> list[EvalItem]:
    tasks = ["KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR"]
    return [
        EvalItem(
            item_id=f"{task}:x{index}",
            sample_id=f"x{index}",
            task=task,
            prompt=f"测试问题 {index}？",
            target="A",
            choices=("A", "B"),
        )
        for index, task in enumerate(tasks)
    ]


def test_public_index_excludes_raw_prompt(tmp_path) -> None:
    path = write_public_index(sample_items(), tmp_path / "index.csv")
    frame = pd.read_csv(path)
    assert len(frame) == 3
    assert "prompt" not in frame.columns
    assert "input_sha256" in frame.columns
    assert frame["input_sha256"].str.len().eq(64).all()


def test_normalized_text_removes_spacing_and_punctuation() -> None:
    assert normalized_text(" 疾病 A？ ") == "疾病a"


def test_audit_defines_regex_screen_limitation() -> None:
    quality, report = audit_items(sample_items())
    assert set(quality["task"]) == {"KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR"}
    assert "does not prove" in report["pii_screen"]["limitation"]
