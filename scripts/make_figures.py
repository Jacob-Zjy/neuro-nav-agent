from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Mandatory publication settings: editable SVG/PDF text and conservative glyph sizes.
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})
plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["legend.frameon"] = False

NAVY = "#0F4D92"
BLUE = "#6F8FC4"
TEAL = "#42949E"
RED = "#B64342"
GOLD = "#D79B32"
GREY = "#A8A8A8"
DARK = "#272727"
PALE = "#E8EEF5"
METHOD_COLORS = [GREY, BLUE, NAVY]


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.04, label, transform=ax.transAxes, fontsize=9,
            fontweight="bold", ha="left", va="bottom")


def save_figure(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix('.svg'), bbox_inches="tight", facecolor="white")
    fig.savefig(output.with_suffix('.pdf'), bbox_inches="tight", facecolor="white")
    fig.savefig(output.with_suffix('.png'), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(output.with_suffix('.tiff'), dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def performance_figure(results: Path, figures: Path) -> None:
    metrics = pd.read_csv(results / "benchmark_metrics.csv")
    methods = metrics["method"].tolist()
    y = np.arange(len(methods))

    fig = plt.figure(figsize=(7.09, 3.35), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.18)

    ax = fig.add_subplot(grid[0, 0])
    values = metrics["balanced_accuracy"].to_numpy()
    lower = values - metrics["ci_low"].to_numpy()
    upper = metrics["ci_high"].to_numpy() - values
    ax.barh(y, values, color=METHOD_COLORS, height=0.58, edgecolor="white")
    ax.errorbar(values, y, xerr=np.vstack([lower, upper]), fmt="none", ecolor=DARK,
                elinewidth=1.0, capsize=2.5, capthick=1.0)
    for yi, value in zip(y, values):
        ax.text(min(value + 0.025, 1.035), yi, f"{value:.3f}", va="center",
                ha="left", fontsize=7, color=DARK)
    ax.set_yticks(y, methods)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Balanced accuracy (95% bootstrap CI)")
    ax.set_title("Controlled local-action benchmark", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.text(0, -0.23, f"n = {int(metrics['n'].iloc[0])} auditable cases; 2,000 bootstrap resamples",
            transform=ax.transAxes, fontsize=6.3, color="#606060")
    panel_label(ax, "a")

    ax = fig.add_subplot(grid[0, 1])
    width = 0.34
    fpr = metrics["false_positive_rate"].to_numpy()
    fnr = metrics["false_negative_rate"].to_numpy()
    ax.bar(y - width / 2, fpr, width, color=RED, label="False positive")
    ax.bar(y + width / 2, fnr, width, color=GOLD, label="False negative")
    ax.set_xticks(y, ["Keyword", "Filters", "NeuroNav"], rotation=18, ha="right",
                  rotation_mode="anchor")
    ax.set_ylim(0, max(0.72, float(max(fpr.max(), fnr.max())) + 0.08))
    ax.set_ylabel("Error rate")
    ax.set_title("Error profile", loc="left", fontweight="bold")
    ax.legend(loc="upper right", fontsize=6.5)
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    panel_label(ax, "b")

    fig.suptitle("Explicit access and eligibility gates prevent controlled navigation errors",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save_figure(fig, figures / "figure1_navigation_performance")


def landscape_figure(results: Path, figures: Path) -> None:
    countries = pd.read_csv(results / "country_counts.csv").head(10).sort_values(
        "n_trial_locations", ascending=True
    )
    statuses = pd.read_csv(results / "status_counts.csv").head(7).sort_values(
        "n_trials", ascending=True
    )
    robustness = pd.read_csv(results / "rank_robustness.csv")
    summary = json.loads((results / "landscape_summary.json").read_text(encoding="utf-8"))

    fig = plt.figure(figsize=(7.09, 4.85), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.0, 0.95], height_ratios=[1.0, 0.9],
                            wspace=0.22, hspace=0.22)

    ax = fig.add_subplot(grid[0, :2])
    colors = [PALE] * len(countries)
    colors[-1] = NAVY
    ax.barh(countries["country"], countries["n_trial_locations"], color=colors,
            edgecolor="white", height=0.68)
    ax.set_xlabel("Trials with at least one registered location")
    ax.set_title("Geographic concentration", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    panel_label(ax, "a")

    ax = fig.add_subplot(grid[0, 2])
    ax.barh(statuses["status"].str.replace("_", " ").str.title(), statuses["n_trials"],
            color=TEAL, edgecolor="white", height=0.62)
    ax.set_xlabel("Trials")
    ax.set_title("Registry status", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    panel_label(ax, "b")

    ax = fig.add_subplot(grid[1, :2])
    robustness = robustness.sort_values(["top_10_probability", "rank"], ascending=[False, True]).head(10)
    y_rank = np.arange(len(robustness))
    probability = robustness["top_10_probability"].to_numpy()
    ax.hlines(y_rank, 0, probability, color=PALE, linewidth=3.0)
    ax.scatter(probability, y_rank, s=30, color=NAVY, edgecolor="white", linewidth=0.6,
               zorder=3)
    for yi, value in zip(y_rank, probability):
        ax.text(min(value + 0.025, 1.025), yi, f"{value:.0%}", va="center", ha="left",
                fontsize=5.8, color=DARK)
    ax.set_yticks(y_rank, [f"Base rank {int(rank)}" for rank in robustness["rank"]])
    ax.invert_yaxis()
    ax.set_xlabel("Probability of remaining in top 10")
    ax.set_xlim(0, 1.08)
    ax.set_title("Ranking robustness under uncertain weights", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.text(0, -0.28, "Access stress test: age 65, female, MCI, Brazil; 2,000 Monte Carlo draws",
            transform=ax.transAxes, fontsize=6.3, color="#606060")
    panel_label(ax, "c")

    ax = fig.add_subplot(grid[1, 2])
    labels = ["Location reported", "Multi-country", "Top-country share"]
    values = [summary["location_completeness"], summary["multi_country_share"],
              summary["top_country_share"]]
    y_positions = np.arange(3)
    ax.barh(y_positions, values, color=[NAVY, TEAL, GREY], height=0.58)
    for index, value in enumerate(values):
        ax.text(value + 0.025, index, f"{value:.0%}", ha="left", va="center", fontsize=6.5)
    ax.set_yticks(y_positions, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Share of trials / locations")
    ax.set_title("Coverage indicators", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#E7E7E7", linewidth=0.6)
    ax.set_axisbelow(True)
    panel_label(ax, "d")

    fig.suptitle("Cognitive-health trial access is uneven, and relevance rankings vary in stability",
                 x=0.01, ha="left", fontsize=10, fontweight="bold")
    save_figure(fig, figures / "figure2_trial_landscape")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    parser.add_argument("--figures", default="figures")
    args = parser.parse_args()
    performance_figure(Path(args.results), Path(args.figures))
    landscape_figure(Path(args.results), Path(args.figures))
    print("Saved two figures in SVG, PDF, PNG, and TIFF formats.")


if __name__ == "__main__":
    main()
