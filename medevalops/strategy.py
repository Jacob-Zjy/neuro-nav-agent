from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import RESULTS_DIR


def _recommend(row: pd.Series) -> str:
    if row["high_confidence_error_rate"] >= 0.25:
        return "优先复核标签规范，补充高置信反例与专家判例"
    if row["support_gap"] >= 0.45:
        return "补齐低频类别样本，并按场景来源做分层采样"
    if row["prompt_disagreement_rate"] >= 0.25:
        return "增加边界对比样本，统一标签定义与标注指南"
    if row["error_pressure"] >= 0.35:
        return "围绕主要混淆对构造最小差异样本和困难负例"
    return "保持监测，抽样复核新增数据与分布漂移"


def build_data_priority(predictions: pd.DataFrame) -> pd.DataFrame:
    pivot = predictions.pivot_table(
        index=["item_id", "task", "target"],
        columns="strategy",
        values=["correct", "confidence", "normalized_entropy", "prediction"],
        aggfunc="first",
    )
    pivot.columns = [f"{metric}_{strategy}" for metric, strategy in pivot.columns]
    pivot = pivot.reset_index()
    pivot["prompt_disagreement"] = pivot["prediction_direct"] != pivot["prediction_rubric"]
    pivot["high_confidence_error"] = (
        ~pivot["correct_rubric"].astype(bool) & (pivot["confidence_rubric"] >= 0.60)
    )

    grouped = (
        pivot.groupby(["task", "target"], observed=True)
        .agg(
            n=("item_id", "size"),
            accuracy_direct=("correct_direct", "mean"),
            accuracy_rubric=("correct_rubric", "mean"),
            mean_confidence=("confidence_rubric", "mean"),
            mean_normalized_entropy=("normalized_entropy_rubric", "mean"),
            prompt_disagreement_rate=("prompt_disagreement", "mean"),
            high_confidence_error_rate=("high_confidence_error", "mean"),
        )
        .reset_index()
    )
    grouped["max_task_support"] = grouped.groupby("task")["n"].transform("max")
    grouped["support_gap"] = 1.0 - grouped["n"] / grouped["max_task_support"]
    grouped["error_pressure"] = 1.0 - grouped["accuracy_rubric"]
    grouped["priority_score"] = (
        0.45 * grouped["error_pressure"]
        + 0.20 * grouped["support_gap"]
        + 0.20 * grouped["mean_normalized_entropy"]
        + 0.15 * grouped["prompt_disagreement_rate"]
    )
    grouped["priority_tier"] = pd.cut(
        grouped["priority_score"],
        bins=[-np.inf, 0.30, 0.50, np.inf],
        labels=["P2-monitor", "P1-improve", "P0-priority"],
    ).astype(str)
    grouped["recommended_action"] = grouped.apply(_recommend, axis=1)
    return grouped.sort_values(["priority_score", "task"], ascending=[False, True])


def write_priority(priority: pd.DataFrame, results_dir: Path = RESULTS_DIR) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "data_priority.csv"
    priority.to_csv(path, index=False)
    return path

