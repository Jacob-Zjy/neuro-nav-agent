from __future__ import annotations

from .models import EvidenceItem, MatchDecision, PatientProfile, TrialRecord
from .normalization import condition_similarity, normalize_country, normalize_sex


RECRUITING_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}

DEFAULT_WEIGHTS = {
    "condition": 0.30,
    "status": 0.25,
    "age": 0.15,
    "sex": 0.10,
    "location": 0.10,
    "completeness": 0.10,
}


def component_scores(profile: PatientProfile, trial: TrialRecord) -> dict[str, float]:
    condition = condition_similarity(profile.condition, trial.conditions)
    status = 1.0 if trial.overall_status in RECRUITING_STATUSES else 0.0

    if profile.age is None:
        age = 0.5
    else:
        above_min = trial.minimum_age_years is None or profile.age >= trial.minimum_age_years
        below_max = trial.maximum_age_years is None or profile.age <= trial.maximum_age_years
        age = 1.0 if above_min and below_max else 0.0

    profile_sex = normalize_sex(profile.sex)
    trial_sex = normalize_sex(trial.sex) or "ALL"
    sex = 0.5 if profile_sex is None else float(trial_sex == "ALL" or profile_sex == trial_sex)

    profile_country = normalize_country(profile.country)
    trial_countries = {normalize_country(country) for country in trial.countries}
    if profile_country is None or not trial_countries:
        location = 0.5
    else:
        location = float(profile_country in trial_countries)

    populated = [
        bool(trial.conditions), trial.minimum_age_years is not None,
        trial.maximum_age_years is not None, bool(trial.sex), bool(trial.countries),
        bool(trial.eligibility_text), bool(trial.interventions), bool(trial.phases),
    ]
    completeness = sum(populated) / len(populated)
    return {
        "condition": condition,
        "status": status,
        "age": age,
        "sex": sex,
        "location": location,
        "completeness": completeness,
    }


def assess_structured(profile: PatientProfile, trial: TrialRecord) -> MatchDecision:
    components = component_scores(profile, trial)
    evidence: list[EvidenceItem] = []
    unresolved: list[str] = []
    hard_failures: list[str] = []

    def add(check: str, outcome: str, explanation: str, *fields: str) -> None:
        evidence.append(EvidenceItem(check, outcome, explanation, tuple(fields)))

    if components["status"] == 0:
        hard_failures.append("Trial is not currently open for navigation.")
        add("recruitment_status", "fail", trial.overall_status, "overall_status")
    else:
        add("recruitment_status", "pass", trial.overall_status, "overall_status")

    if components["condition"] < 0.34:
        hard_failures.append("Target condition does not match the registered conditions.")
        add("condition", "fail", "Low condition overlap.", "conditions")
    else:
        add("condition", "pass", f"Condition overlap={components['condition']:.2f}.", "conditions")

    if profile.age is None:
        unresolved.append("Age was not supplied.")
        add("age", "unknown", "Age requires clarification.", "minimum_age_years", "maximum_age_years")
    elif components["age"] == 0:
        hard_failures.append("Age is outside the registered range.")
        add("age", "fail", f"Profile age={profile.age:g}.", "minimum_age_years", "maximum_age_years")
    else:
        add("age", "pass", f"Profile age={profile.age:g}.", "minimum_age_years", "maximum_age_years")

    if profile.sex is None:
        unresolved.append("Sex was not supplied.")
        add("sex", "unknown", "Sex requires clarification.", "sex")
    elif components["sex"] == 0:
        hard_failures.append("Sex does not match the registered criterion.")
        add("sex", "fail", f"Trial criterion={trial.sex}.", "sex")
    else:
        add("sex", "pass", f"Trial criterion={trial.sex}.", "sex")

    if profile.country is None:
        unresolved.append("Country was not supplied.")
        add("location", "unknown", "Location requires clarification.", "countries")
    elif components["location"] == 0:
        add("location", "caution", "No registered site in the requested country.", "countries")
    else:
        add("location", "pass", "A registered site is available in the requested country.", "countries")

    unresolved.append("Free-text inclusion and exclusion criteria require coordinator review.")
    base_score = sum(DEFAULT_WEIGHTS[key] * value for key, value in components.items())
    if hard_failures:
        base_score *= 0.05
    return MatchDecision(
        nct_id=trial.nct_id,
        status="not_match" if hard_failures else "potential_match",
        base_score=round(float(base_score), 6),
        components=components,
        evidence=tuple(evidence),
        unresolved=tuple(hard_failures + unresolved),
        clinical_review_required=True,
    )

