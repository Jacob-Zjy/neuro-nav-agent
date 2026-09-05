from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import TrialRecord


TUPLE_FIELDS = {"conditions", "countries", "phases", "interventions"}


def save_trials(path: str | Path, trials: Iterable[TrialRecord]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for trial in trials:
        row = trial.as_dict()
        for field in TUPLE_FIELDS:
            row[field] = json.dumps(row[field], ensure_ascii=False)
        rows.append(row)
    if not rows:
        raise ValueError("Refusing to write an empty trial snapshot.")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_trials(path: str | Path) -> list[TrialRecord]:
    path = Path(path)
    trials = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            for field in TUPLE_FIELDS:
                row[field] = tuple(json.loads(row[field] or "[]"))
            for field in ("minimum_age_years", "maximum_age_years"):
                row[field] = float(row[field]) if row[field] else None
            trials.append(TrialRecord(**row))
    return trials


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def write_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(value), ensure_ascii=False, indent=2), encoding="utf-8")

