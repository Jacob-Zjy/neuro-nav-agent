from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
})
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["legend.frameon"] = False

DIRECT = "#7884B4"
RUBRIC = "#D24B40"
NEUTRAL = "#606060"
TEAL = "#42949E"
LIGHT = "#E8ECF4"

TASK_LABELS = {
    "KUAKE-QIC": "Intent",
    "KUAKE-QQR": "Query relation",
    "KUAKE-QTR": "Title relevance",
    "Overall": "Overall",
}

LABEL_MAP = {
    "疾病描述": "Disease description",
    "疾病表述": "Disease description",
    "指标解读": "Result interpretation",
    "医疗费用": "Cost",
    "治疗方案": "Treatment",
    "功效作用": "Effect",
    "病情诊断": "Diagnosis",
    "非上述类型": "Other",
    "注意事项": "Precaution",
    "病因分析": "Cause",
    "就医建议": "Care seeking",
    "后果表述": "Prognosis",
    "完全一致": "Equivalent",
    "后者是前者的语义子集": "Q2 subset",
    "后者是前者的语义父集": "Q2 superset",
    "语义无直接关联": "Unrelated",
    "完全不匹配或者没有参考价值": "No match",
    "很少匹配有一些参考价值": "Weak match",
    "部分匹配": "Partial match",
    "完全匹配": "Exact match",
}


def _panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.13,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
    )


def _save(fig: plt.Figure, base: Path) -> list[Path]:
    base.parent.mkdir(parents=True, exist_ok=True)
    svg_path = base.with_suffix(".svg")
    pdf_path = base.with_suffix(".pdf")
    png_path = base.with_suffix(".png")
    tiff_path = base.with_suffix(".tiff")
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(
        tiff_path,
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return [svg_path, pdf_path, png_path, tiff_path]


def performance_figure(
    summary: pd.DataFrame, comparison: pd.DataFrame, output_dir: Path
) -> list[Path]:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.2))
    tasks = ["KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR", "Overall"]
    x = np.arange(len(tasks))

    for ax, metric, ylabel, panel in [
        (axes[0, 0], "accuracy", "Accuracy", "a"),
        (axes[0, 1], "macro_f1", "Macro-F1", "b"),
    ]:
        for offset, strategy, color, label in [
            (-0.08, "direct", DIRECT, "Direct prompt"),
            (0.08, "rubric", RUBRIC, "Rubric prompt"),
        ]:
            subset = summary[summary["strategy"].eq(strategy)].set_index("task").loc[tasks]
            center = subset[metric].to_numpy()
            low = center - subset[f"{metric}_ci_low"].to_numpy()
            high = subset[f"{metric}_ci_high"].to_numpy() - center
            ax.errorbar(
                x + offset,
                center,
                yerr=np.vstack([low, high]),
                fmt="o",
                color=color,
                capsize=2.5,
                lw=1.3,
                ms=4,
                label=label,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [TASK_LABELS[task] for task in tasks],
            rotation=20,
            ha="right",
            rotation_mode="anchor",
        )
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 1.02)
        ax.grid(axis="y", color="#E4E4E4", lw=0.6)
        _panel(ax, panel)
    axes[0, 0].legend(loc="lower left")

    ax = axes[1, 0]
    comp = comparison.set_index("task").loc[tasks[:-1]]
    y = np.arange(len(comp))[::-1]
    for yi, (_, row) in zip(y, comp.iterrows()):
        ax.plot([row.delta_ci_low, row.delta_ci_high], [yi, yi], color=RUBRIC, lw=1.6)
        ax.plot(row.accuracy_delta, yi, "o", color=RUBRIC, ms=4)
    ax.axvline(0, color=NEUTRAL, lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels([TASK_LABELS[task] for task in comp.index])
    ax.set_xlabel("Accuracy change: rubric - direct")
    ax.grid(axis="x", color="#E4E4E4", lw=0.6)
    _panel(ax, "c")

    ax = axes[1, 1]
    reliability = summary[summary["task"].eq("Overall")].set_index("strategy")
    width = 0.34
    metric_x = np.arange(2)
    ax.bar(
        metric_x - width / 2,
        [reliability.loc["direct", "ece_10"], reliability.loc["direct", "brier_multiclass"]],
        width,
        color=DIRECT,
        label="Direct prompt",
    )
    ax.bar(
        metric_x + width / 2,
        [reliability.loc["rubric", "ece_10"], reliability.loc["rubric", "brier_multiclass"]],
        width,
        color=RUBRIC,
        label="Rubric prompt",
    )
    ax.set_xticks(metric_x)
    ax.set_xticklabels(["ECE (10 bins)", "Multiclass Brier"])
    ax.set_ylabel("Lower is better")
    ax.grid(axis="y", color="#E4E4E4", lw=0.6)
    _panel(ax, "d")

    fig.suptitle(
        "Prompt strategy changes performance and confidence reliability",
        fontsize=10,
        fontweight="bold",
        x=0.05,
        ha="left",
    )
    fig.text(
        0.05,
        0.005,
        "Points show item-level estimates; intervals are 95% percentile bootstrap CIs (2,000 resamples).",
        fontsize=6,
        color=NEUTRAL,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.95], h_pad=2.2, w_pad=2.0)
    return _save(fig, output_dir / "figure1_performance_reliability")


def _matrix_for_task(frame: pd.DataFrame, task: str, strategy: str) -> tuple[np.ndarray, list[str]]:
    subset = frame[(frame["task"].eq(task)) & (frame["strategy"].eq(strategy))]
    labels = sorted(set(subset["target"]) | set(subset["prediction"]))
    matrix = np.zeros((len(labels), len(labels)), dtype=float)
    index = {label: position for position, label in enumerate(labels)}
    for row in subset.itertuples(index=False):
        matrix[index[row.target], index[row.prediction]] += 1
    row_sums = matrix.sum(axis=1, keepdims=True)
    matrix = np.divide(matrix, row_sums, out=np.zeros_like(matrix), where=row_sums != 0)
    return matrix, [LABEL_MAP.get(label, label) for label in labels]


def confusion_figure(predictions: pd.DataFrame, output_dir: Path) -> list[Path]:
    tasks = ["KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.05), gridspec_kw={"width_ratios": [1.7, 1, 1]})
    image = None
    for panel, ax, task in zip("abc", axes, tasks):
        matrix, labels = _matrix_for_task(predictions, task, "rubric")
        image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=55, ha="right", rotation_mode="anchor", fontsize=5.2)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=5.2)
        ax.set_title(TASK_LABELS[task], fontsize=8, pad=6)
        ax.set_xlabel("Predicted label")
        if panel == "a":
            ax.set_ylabel("Reference label")
        for (row, col), value in np.ndenumerate(matrix):
            if value >= 0.08:
                ax.text(
                    col,
                    row,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=5.0,
                    color="white" if value > 0.55 else "#272727",
                )
        _panel(ax, panel)
    if image is not None:
        colorbar = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02)
        colorbar.set_label("Row-normalized fraction")
    fig.suptitle(
        "Error structure under the rubric prompt",
        fontsize=10,
        fontweight="bold",
        x=0.05,
        ha="left",
    )
    fig.subplots_adjust(left=0.12, right=0.91, bottom=0.31, top=0.82, wspace=0.58)
    return _save(fig, output_dir / "figure2_confusion_structure")


def priority_figure(priority: pd.DataFrame, quality: pd.DataFrame, output_dir: Path) -> list[Path]:
    top = priority.head(14).sort_values("priority_score")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.65), gridspec_kw={"width_ratios": [1.35, 1]})

    ax = axes[0]
    colors = [RUBRIC if tier == "P0-priority" else TEAL for tier in top["priority_tier"]]
    labels = [f"{TASK_LABELS[task]} · {LABEL_MAP.get(label, label)}" for task, label in zip(top.task, top.target)]
    ax.barh(np.arange(len(top)), top["priority_score"], color=colors)
    ax.set_yticks(np.arange(len(top)))
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_xlabel("Data-priority score (heuristic)")
    ax.grid(axis="x", color="#E4E4E4", lw=0.6)
    _panel(ax, "a")

    ax = axes[1]
    for task, marker in zip(["KUAKE-QIC", "KUAKE-QQR", "KUAKE-QTR"], ["o", "s", "^"]):
        subset = priority[priority["task"].eq(task)]
        ax.scatter(
            1 - subset["accuracy_rubric"],
            subset["mean_normalized_entropy"],
            s=16 + subset["n"] * 0.45,
            c=subset["priority_score"],
            cmap="Reds",
            vmin=0,
            vmax=max(0.65, float(priority["priority_score"].max())),
            marker=marker,
            edgecolor="white",
            linewidth=0.5,
            label=TASK_LABELS[task],
        )
    ax.set_xlabel("Rubric-prompt error rate")
    ax.set_ylabel("Mean normalized entropy")
    ax.grid(color="#E4E4E4", lw=0.6)
    ax.legend(loc="lower right", fontsize=6)
    _panel(ax, "b")

    fig.suptitle(
        "Observed failure patterns become concrete data actions",
        fontsize=10,
        fontweight="bold",
        x=0.05,
        ha="left",
    )
    fig.text(
        0.05,
        0.015,
        "Priority = 45% error + 20% support gap + 20% uncertainty + 15% prompt disagreement. Bubble area reflects item count.",
        fontsize=6,
        color=NEUTRAL,
    )
    fig.tight_layout(rect=[0, 0.045, 1, 0.92], w_pad=2.4)
    return _save(fig, output_dir / "figure3_data_priority")
