from __future__ import annotations

import re


_AGE_UNITS_IN_YEARS = {
    "year": 1.0,
    "years": 1.0,
    "month": 1.0 / 12.0,
    "months": 1.0 / 12.0,
    "week": 1.0 / 52.1429,
    "weeks": 1.0 / 52.1429,
    "day": 1.0 / 365.2425,
    "days": 1.0 / 365.2425,
}

_COUNTRY_ALIASES = {
    "usa": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "us": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "pr china": "china",
    "people's republic of china": "china",
}

_CONDITION_EXPANSIONS = {
    "mci": {"mild", "cognitive", "impairment"},
    "alzheimer": {"alzheimer", "alzheimers", "dementia", "cognitive"},
    "alzheimers": {"alzheimer", "alzheimers", "dementia", "cognitive"},
    "dementia": {"dementia", "cognitive", "alzheimer"},
    "cognitive": {"cognitive", "cognition"},
}

_STOPWORDS = {
    "and", "or", "of", "the", "disease", "disorder", "syndrome",
    "condition", "unspecified", "with", "without", "due", "to",
}


def parse_age_years(value: str | int | float | None) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)?", value.strip())
    if not match:
        return None
    amount = float(match.group(1))
    unit = (match.group(2) or "years").lower()
    factor = _AGE_UNITS_IN_YEARS.get(unit)
    return None if factor is None else amount * factor


def normalize_sex(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().upper()
    aliases = {"M": "MALE", "MAN": "MALE", "F": "FEMALE", "WOMAN": "FEMALE"}
    return aliases.get(normalized, normalized)


def normalize_country(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    return _COUNTRY_ALIASES.get(normalized, normalized)


def condition_tokens(value: str) -> set[str]:
    tokens = {
        token for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in _STOPWORDS and len(token) > 1
    }
    expanded = set(tokens)
    frontier = set(tokens)
    while frontier:
        token = frontier.pop()
        additions = _CONDITION_EXPANSIONS.get(token, set()) - expanded
        expanded.update(additions)
        frontier.update(additions)
    return expanded


def condition_similarity(query: str, trial_conditions: tuple[str, ...]) -> float:
    query_tokens = condition_tokens(query)
    if not query_tokens:
        return 0.0
    best = 0.0
    for condition in trial_conditions:
        candidate = condition_tokens(condition)
        if not candidate:
            continue
        overlap = len(query_tokens & candidate)
        denominator = max(1, min(len(query_tokens), len(candidate)))
        best = max(best, overlap / denominator)
    return min(best, 1.0)
