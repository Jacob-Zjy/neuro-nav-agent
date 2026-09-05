"""Check consistency of the committed public release artifacts."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class _PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.section_count = 0
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        elif tag == "section":
            self.section_count += 1
        elif tag == "img" and attributes.get("src"):
            self.images.append(str(attributes["src"]))


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    trials_path = ROOT / "data" / "processed" / "trials_snapshot.csv"
    cases_path = ROOT / "data" / "benchmark" / "cases.jsonl"
    data_meta = _read_json(ROOT / "data" / "metadata.json")
    benchmark_meta = _read_json(ROOT / "data" / "benchmark" / "metadata.json")
    trials = pd.read_csv(trials_path)
    metrics = pd.read_csv(ROOT / "results" / "benchmark_metrics.csv")
    robustness = pd.read_csv(ROOT / "results" / "rank_robustness.csv")

    _require(len(trials) == int(data_meta["records"]), "Trial count differs from metadata")
    _require(trials["nct_id"].notna().all(), "Missing NCT identifier")
    _require(trials["nct_id"].is_unique, "Duplicate NCT identifier")
    _require(
        trials["source_url"].str.startswith("https://clinicaltrials.gov/study/").all(),
        "Unexpected trial source URL",
    )
    case_count = sum(1 for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip())
    _require(case_count == int(benchmark_meta["n_cases"]), "Benchmark count differs from metadata")
    _require((metrics["n"] == case_count).all(), "Metric sample sizes differ from benchmark")
    _require(
        set(metrics["method"]) == {"Keyword retrieval", "Structured filters", "NeuroNav-Agent"},
        "Expected benchmark methods are missing",
    )
    metric_columns = [
        "accuracy", "balanced_accuracy", "ci_low", "ci_high", "precision",
        "recall", "specificity", "f1", "false_positive_rate", "false_negative_rate",
    ]
    _require(metrics[metric_columns].apply(lambda column: column.between(0, 1).all()).all(), "Metric outside [0, 1]")
    _require((metrics["ci_low"] <= metrics["balanced_accuracy"]).all(), "Invalid lower confidence bound")
    _require((metrics["balanced_accuracy"] <= metrics["ci_high"]).all(), "Invalid upper confidence bound")
    _require(robustness["top_10_probability"].between(0, 1).all(), "Invalid ranking probability")

    required_figure_stems = ["figure1_navigation_performance", "figure2_trial_landscape"]
    for stem in required_figure_stems:
        for suffix in (".svg", ".pdf", ".png", ".tiff"):
            _require((ROOT / "figures" / f"{stem}{suffix}").is_file(), f"Missing figure export: {stem}{suffix}")

    html_path = ROOT / "docs" / "index.html"
    html_text = html_path.read_text(encoding="utf-8")
    page = _PageAudit()
    page.feed(html_text)
    _require(page.h1_count == 1, "Project guide must have exactly one H1")
    _require(page.section_count >= 4, "Project guide has too few content sections")
    _require(len(page.images) >= 2, "Project guide must show both result figures")
    for image in page.images:
        _require((html_path.parent / image).resolve().is_file(), f"Broken project-guide image: {image}")

    searchable = html_text + (ROOT / "README.md").read_text(encoding="utf-8")
    _require(not any(marker in searchable.lower() for marker in ("todo", "tbd", "lorem ipsum")), "Placeholder text remains")
    _read_json(ROOT / "results" / "sample_navigation_report.json")

    summary = {
        "trial_records": len(trials),
        "synthetic_benchmark_cases": case_count,
        "methods": metrics["method"].tolist(),
        "html_sections": page.section_count,
        "html_images": len(page.images),
        "figure_exports": 8,
        "status": "PASS",
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
