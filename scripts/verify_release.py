from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from medevalops.config import PROJECT_ROOT, SOURCE_SHA256, STRATEGIES, TASKS
from medevalops.data import sha256_file

EXPECTED_ITEMS = 1240


def require(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise AssertionError(f"Missing or empty artifact: {path}")


def main() -> None:
    required = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "RESULTS.md",
        PROJECT_ROOT / "EVALUATION_CARD.md",
        PROJECT_ROOT / "data" / "processed" / "public_item_index.csv",
        PROJECT_ROOT / "data" / "processed" / "source_manifest.json",
        PROJECT_ROOT / "results" / "predictions.csv",
        PROJECT_ROOT / "results" / "summary_metrics.csv",
        PROJECT_ROOT / "results" / "paired_comparison.csv",
        PROJECT_ROOT / "results" / "data_priority.csv",
        PROJECT_ROOT / "results" / "data_quality.csv",
        PROJECT_ROOT / "results" / "data_audit.json",
        PROJECT_ROOT / "results" / "run_metadata.json",
        PROJECT_ROOT / "docs" / "index.html",
    ]
    for stem in [
        "figure1_performance_reliability",
        "figure2_confusion_structure",
        "figure3_data_priority",
    ]:
        for suffix in [".svg", ".pdf", ".png", ".tiff"]:
            required.append(PROJECT_ROOT / "figures" / f"{stem}{suffix}")
    for path in required:
        require(path)

    index = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "public_item_index.csv")
    if len(index) != EXPECTED_ITEMS or index["item_id"].nunique() != EXPECTED_ITEMS:
        raise AssertionError("Public index item count or uniqueness mismatch")
    forbidden_index = {"input", "prompt", "query", "text", "raw_text"} & set(index.columns)
    if forbidden_index:
        raise AssertionError(f"Public index leaks raw text columns: {sorted(forbidden_index)}")

    predictions = pd.read_csv(PROJECT_ROOT / "results" / "predictions.csv")
    if len(predictions) != EXPECTED_ITEMS * len(STRATEGIES):
        raise AssertionError("Prediction row count mismatch")
    if predictions.duplicated(["item_id", "strategy"]).any():
        raise AssertionError("Duplicate item/strategy predictions")
    if set(predictions["task"]) != set(TASKS):
        raise AssertionError("Unexpected task set")
    forbidden_prediction = {"input", "prompt", "query", "text", "raw_text"} & set(
        predictions.columns
    )
    if forbidden_prediction:
        raise AssertionError(
            f"Predictions leak raw text columns: {sorted(forbidden_prediction)}"
        )

    metadata = json.loads(
        (PROJECT_ROOT / "results" / "run_metadata.json").read_text(encoding="utf-8")
    )
    if metadata["items"] != EXPECTED_ITEMS or metadata["predictions"] != EXPECTED_ITEMS * 2:
        raise AssertionError("Run metadata count mismatch")
    source_manifest = json.loads(
        (PROJECT_ROOT / "data" / "processed" / "source_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if source_manifest["source_sha256"].lower() != SOURCE_SHA256:
        raise AssertionError("Source manifest hash mismatch")

    raw = PROJECT_ROOT / "data" / "raw" / "promptcblue_validation.parquet"
    if raw.exists() and sha256_file(raw) != SOURCE_SHA256:
        raise AssertionError("Local raw source hash mismatch")

    page = (PROJECT_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    for marker in ["1,240", "Qwen3-0.6B", "Data strategy", "不是临床能力证明"]:
        if marker not in page:
            raise AssertionError(f"Site marker missing: {marker}")
    print(f"Release verified: {len(required)} required artifacts; {len(predictions)} predictions")


if __name__ == "__main__":
    main()

