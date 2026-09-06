from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

from .config import (
    EXPECTED_TASK_ROWS,
    PROCESSED_DIR,
    RAW_DIR,
    SOURCE_FILENAME,
    SOURCE_ROWS,
    SOURCE_SHA256,
    SOURCE_URL,
    TASKS,
)


@dataclass(frozen=True)
class EvalItem:
    item_id: str
    sample_id: str
    task: str
    prompt: str
    target: str
    choices: tuple[str, ...]

    @property
    def input_sha256(self) -> str:
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_source(destination: Path | None = None, *, force: bool = False) -> Path:
    destination = destination or RAW_DIR / SOURCE_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        actual = sha256_file(destination)
        if actual == SOURCE_SHA256:
            return destination
        raise ValueError(
            f"Existing source hash mismatch: expected {SOURCE_SHA256}, got {actual}. "
            "Use --force only after checking the upstream revision."
        )

    temporary = destination.with_suffix(destination.suffix + ".part")
    with requests.get(SOURCE_URL, stream=True, timeout=120) as response:
        response.raise_for_status()
        with temporary.open("wb") as stream:
            for block in response.iter_content(chunk_size=1024 * 1024):
                if block:
                    stream.write(block)
    actual = sha256_file(temporary)
    if actual != SOURCE_SHA256:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"Downloaded source hash mismatch: {actual}")
    temporary.replace(destination)
    return destination


def _as_choices(value: Any) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value)
    raise TypeError(f"answer_choices must be a list-like value, got {type(value)!r}")


def canonicalize_label(task: str, label: str) -> str:
    """Normalize a documented PromptCBLUE QIC label alias."""
    label = label.strip()
    if task == "KUAKE-QIC" and label == "疾病表述":
        return "疾病描述"
    return label


def load_source(path: Path | None = None) -> pd.DataFrame:
    path = path or RAW_DIR / SOURCE_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Source data not found: {path}. Run scripts/download_data.py first.")
    actual = sha256_file(path)
    if actual != SOURCE_SHA256:
        raise ValueError(f"Source hash mismatch: expected {SOURCE_SHA256}, got {actual}")
    frame = pd.read_parquet(path)
    required = {"input", "target", "answer_choices", "task_dataset", "sample_id"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Source data missing columns: {sorted(missing)}")
    if len(frame) != SOURCE_ROWS:
        raise ValueError(f"Expected {SOURCE_ROWS} source rows, got {len(frame)}")
    return frame


def build_items(frame: pd.DataFrame) -> list[EvalItem]:
    selected = frame[frame["task_dataset"].isin(TASKS)].copy()
    counts = selected["task_dataset"].value_counts().to_dict()
    if counts != EXPECTED_TASK_ROWS:
        raise ValueError(f"Unexpected task row counts: {counts}")

    items: list[EvalItem] = []
    for row in selected.itertuples(index=False):
        task = str(row.task_dataset)
        choices = tuple(canonicalize_label(task, choice) for choice in _as_choices(row.answer_choices))
        choices = tuple(dict.fromkeys(choices))
        target = canonicalize_label(task, str(row.target))
        # PromptCBLUE defines an implicit reject option for KUAKE-QIC: the
        # correct answer can be "非上述类型" even when that phrase is omitted
        # from the row-level answer_choices list and rendered prompt.
        if task == "KUAKE-QIC" and "非上述类型" not in choices:
            choices = (*choices, "非上述类型")
        if not choices or target not in choices:
            raise ValueError(f"Invalid choices/target for {row.task_dataset}:{row.sample_id}")
        sample_id = str(row.sample_id)
        prompt = str(row.input).strip()
        if task == "KUAKE-QIC":
            prompt = prompt.replace("疾病表述", "疾病描述")
        items.append(
            EvalItem(
                item_id=f"{task}:{sample_id}",
                sample_id=sample_id,
                task=task,
                prompt=prompt,
                target=target,
                choices=choices,
            )
        )
    if len({item.item_id for item in items}) != len(items):
        raise ValueError("item_id is not unique")
    return items


def write_private_items(items: Iterable[EvalItem], path: Path | None = None) -> Path:
    path = path or PROCESSED_DIR / "eval_items.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for item in items:
            payload = asdict(item)
            payload["choices"] = list(item.choices)
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def read_private_items(path: Path | None = None) -> list[EvalItem]:
    path = path or PROCESSED_DIR / "eval_items.jsonl"
    items: list[EvalItem] = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            payload = json.loads(line)
            payload["choices"] = tuple(payload["choices"])
            items.append(EvalItem(**payload))
    return items


def normalized_text(text: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text.lower())


def write_public_index(items: Iterable[EvalItem], path: Path | None = None) -> Path:
    path = path or PROCESSED_DIR / "public_item_index.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "item_id": item.item_id,
            "sample_id": item.sample_id,
            "task": item.task,
            "target": item.target,
            "choice_count": len(item.choices),
            "character_count": len(item.prompt),
            "input_sha256": item.input_sha256,
            "normalized_sha256": hashlib.sha256(
                normalized_text(item.prompt).encode("utf-8")
            ).hexdigest(),
        }
        for item in items
    ]
    pd.DataFrame(rows).sort_values(["task", "sample_id"]).to_csv(path, index=False)
    return path
