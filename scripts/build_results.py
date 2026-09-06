from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from medevalops.config import PROJECT_ROOT, RESULTS_DIR


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    summary = pd.read_csv(RESULTS_DIR / "summary_metrics.csv")
    comparison = pd.read_csv(RESULTS_DIR / "paired_comparison.csv")
    metadata = json.loads((RESULTS_DIR / "run_metadata.json").read_text(encoding="utf-8"))
    priority = pd.read_csv(RESULTS_DIR / "data_priority.csv")

    lines = [
        "# 实验结果",
        "",
        "> 本页由 `python -m scripts.build_results` 从结果文件自动生成。",
        "",
        "## 运行信息",
        "",
        f"- 模型：`{metadata['model']}`",
        f"- 模型 revision：`{metadata['model_revision']}`",
        f"- 设备：`{metadata['device']}` / `{metadata.get('gpu') or 'CPU'}`",
        f"- 独立评测条目：{metadata['items']}",
        f"- 条件似然序列：{metadata['candidate_sequences']}",
        f"- 推理耗时：{metadata['elapsed_seconds']:.1f} 秒",
        "",
        "## 总体与分任务结果",
        "",
        "| 任务 | 提示 | n | Accuracy (95% CI) | Macro-F1 (95% CI) | ECE | Brier |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.task} | {row.strategy} | {row.n} | "
            f"{row.accuracy:.3f} [{row.accuracy_ci_low:.3f}, {row.accuracy_ci_high:.3f}] | "
            f"{row.macro_f1:.3f} [{row.macro_f1_ci_low:.3f}, {row.macro_f1_ci_high:.3f}] | "
            f"{row.ece_10:.3f} | {row.brier_multiclass:.3f} |"
        )

    lines.extend(
        [
            "",
            "## 提示策略配对比较",
            "",
            "| 任务 | Accuracy 变化 | 95% CI | McNemar p | BH-adjusted p | 不一致条目 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.task} | {row.accuracy_delta:+.3f} | "
            f"[{row.delta_ci_low:+.3f}, {row.delta_ci_high:+.3f}] | "
            f"{row.mcnemar_exact_p:.4g} | {row.mcnemar_bh_p:.4g} | {row.discordant} |"
        )

    lines.extend(
        [
            "",
            "## 优先数据切片",
            "",
            "| 优先级 | 任务 | 标签 | n | 规则提示准确率 | 提示不一致率 | 优先级分数 | 建议动作 |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in priority.head(12).itertuples(index=False):
        lines.append(
            f"| {row.priority_tier} | {row.task} | {row.target} | {row.n} | "
            f"{pct(row.accuracy_rubric)} | {pct(row.prompt_disagreement_rate)} | "
            f"{row.priority_score:.3f} | {row.recommended_action} |"
        )

    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- `n` 是独立 benchmark 条目数，不是患者数。",
            "- 置信区间来自 item-level bootstrap，仅反映评测条目抽样不确定性。",
            "- 分任务比较为同条目配对，使用双侧精确 McNemar 检验，并对三项检验进行 Benjamini-Hochberg 校正。",
            "- 分数只适用于当前模型、模型 revision、数据子集、提示与强制标签评分协议。",
            "- 公开 benchmark 可能进入模型训练数据，结果不能视为未污染的临床能力证据。",
            "- 数据优先级是透明的运营启发式，不是医疗风险评分。",
            "",
        ]
    )
    output = PROJECT_ROOT / "RESULTS.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

