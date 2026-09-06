from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from .config import RESULTS_DIR, SOURCE_SHA256, SOURCE_URL, TASKS
from .data import EvalItem, normalized_text

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
CN_ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def _normalized_entropy(counts: Counter[str]) -> float:
    probabilities = np.asarray(list(counts.values()), dtype=float)
    probabilities /= probabilities.sum()
    entropy = float(-(probabilities * np.log(probabilities)).sum())
    return entropy / math.log(len(counts)) if len(counts) > 1 else 0.0


def audit_items(items: list[EvalItem]) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    for task in TASKS:
        task_items = [item for item in items if item.task == task]
        normalized = [normalized_text(item.prompt) for item in task_items]
        label_counts = Counter(item.target for item in task_items)
        rows.append(
            {
                "task": task,
                "n": len(task_items),
                "labels": len(label_counts),
                "unique_exact_rate": len({item.prompt for item in task_items}) / len(task_items),
                "unique_normalized_rate": len(set(normalized)) / len(task_items),
                "largest_class_share": max(label_counts.values()) / len(task_items),
                "label_entropy_normalized": _normalized_entropy(label_counts),
                "mean_character_count": np.mean([len(item.prompt) for item in task_items]),
                "p95_character_count": np.quantile(
                    [len(item.prompt) for item in task_items], 0.95
                ),
                "invalid_target_count": sum(
                    item.target not in item.choices for item in task_items
                ),
                "email_pattern_hits": sum(bool(EMAIL_RE.search(item.prompt)) for item in task_items),
                "phone_pattern_hits": sum(bool(PHONE_RE.search(item.prompt)) for item in task_items),
                "cn_id_pattern_hits": sum(bool(CN_ID_RE.search(item.prompt)) for item in task_items),
            }
        )

    all_normalized = [normalized_text(item.prompt) for item in items]
    repeated = Counter(all_normalized)
    cross_task_duplicates = 0
    for text, count in repeated.items():
        if count < 2:
            continue
        tasks = {item.task for item in items if normalized_text(item.prompt) == text}
        if len(tasks) > 1:
            cross_task_duplicates += 1

    report = {
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_SHA256,
        "selected_tasks": list(TASKS),
        "selected_rows": len(items),
        "unique_item_ids": len({item.item_id for item in items}),
        "cross_task_normalized_duplicate_groups": cross_task_duplicates,
        "pii_screen": {
            "scope": "Regex screen for email, mainland China mobile number, and PRC ID patterns only",
            "limitation": "A zero count does not prove that the text is de-identified.",
            "email_pattern_hits": sum(bool(EMAIL_RE.search(item.prompt)) for item in items),
            "phone_pattern_hits": sum(bool(PHONE_RE.search(item.prompt)) for item in items),
            "cn_id_pattern_hits": sum(bool(CN_ID_RE.search(item.prompt)) for item in items),
        },
        "publication_policy": (
            "Raw prompt text stays outside git. Public artifacts contain hashes, labels, "
            "predictions, aggregate metrics, and a reproducible download script."
        ),
    }
    return pd.DataFrame(rows), report


def write_audit_outputs(
    quality: pd.DataFrame,
    report: dict[str, object],
    results_dir: Path = RESULTS_DIR,
) -> tuple[Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    quality_path = results_dir / "data_quality.csv"
    report_path = results_dir / "data_audit.json"
    quality.to_csv(quality_path, index=False)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality_path, report_path

