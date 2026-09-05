from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .eligibility import RECRUITING_STATUSES
from .models import PatientProfile, TrialRecord
from .normalization import condition_similarity


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    trial_nct_id: str
    profile: PatientProfile
    expected_match: bool
    perturbation: str


def _representative_age(trial: TrialRecord) -> float:
    low = trial.minimum_age_years if trial.minimum_age_years is not None else 50.0
    high = trial.maximum_age_years if trial.maximum_age_years is not None else 80.0
    return round((low + high) / 2.0, 1)


def generate_benchmark(trials: list[TrialRecord], max_trials: int = 120) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    usable = [
        trial for trial in trials
        if trial.overall_status in RECRUITING_STATUSES and trial.conditions and trial.countries
    ][:max_trials]
    for index, trial in enumerate(usable):
        condition = trial.conditions[0]
        sex = "female" if trial.sex == "ALL" else trial.sex.lower()
        country = trial.countries[0] if trial.countries else "United States"
        positive = PatientProfile(condition, _representative_age(trial), sex, country)
        cases.append(BenchmarkCase(f"P{index:03d}", trial.nct_id, positive, True, "none"))

        unrelated = "Type 2 Diabetes"
        if condition_similarity(unrelated, trial.conditions) >= 0.34:
            unrelated = "Chronic Kidney Disease"
        cases.append(BenchmarkCase(
            f"C{index:03d}", trial.nct_id,
            PatientProfile(unrelated, positive.age, sex, country), False, "condition_mismatch"
        ))

        country_candidates = (
            "China", "United States", "United Kingdom", "Canada", "Australia", "Brazil"
        )
        unavailable_country = next(
            candidate for candidate in country_candidates if candidate not in trial.countries
        )
        cases.append(BenchmarkCase(
            f"L{index:03d}", trial.nct_id,
            PatientProfile(condition, positive.age, sex, unavailable_country),
            False, "no_registered_local_site"
        ))

        if trial.minimum_age_years is not None and trial.minimum_age_years >= 1:
            age = max(0.0, trial.minimum_age_years - 1.0)
            cases.append(BenchmarkCase(
                f"A{index:03d}", trial.nct_id,
                PatientProfile(condition, age, sex, country), False, "age_below_minimum"
            ))
        elif trial.maximum_age_years is not None:
            cases.append(BenchmarkCase(
                f"A{index:03d}", trial.nct_id,
                PatientProfile(condition, trial.maximum_age_years + 1.0, sex, country),
                False, "age_above_maximum"
            ))

        if trial.sex in {"MALE", "FEMALE"}:
            opposite = "female" if trial.sex == "MALE" else "male"
            cases.append(BenchmarkCase(
                f"S{index:03d}", trial.nct_id,
                PatientProfile(condition, positive.age, opposite, country), False, "sex_mismatch"
            ))
    if not cases:
        raise ValueError("No recruiting trials were available for benchmark generation.")
    return cases


def save_benchmark(path: str | Path, cases: list[BenchmarkCase]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            row = asdict(case)
            row["profile"] = asdict(case.profile)
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_benchmark(path: str | Path) -> list[BenchmarkCase]:
    cases = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            row["profile"] = PatientProfile(**row["profile"])
            cases.append(BenchmarkCase(**row))
    return cases
