from __future__ import annotations

import numpy as np

from .eligibility import DEFAULT_WEIGHTS, assess_structured
from .models import MatchDecision, PatientProfile, RankedTrial, TrialRecord


def rank_trials(profile: PatientProfile, trials: list[TrialRecord]) -> list[RankedTrial]:
    pairs: list[tuple[TrialRecord, MatchDecision]] = []
    for trial in trials:
        decision = assess_structured(profile, trial)
        if decision.status == "potential_match":
            pairs.append((trial, decision))
    pairs.sort(key=lambda pair: (-pair[1].base_score, pair[0].nct_id))
    return [
        RankedTrial(trial=trial, decision=decision, rank=index + 1)
        for index, (trial, decision) in enumerate(pairs)
    ]


def rank_robustness(
    profile: PatientProfile,
    trials: list[TrialRecord],
    top_k: int = 5,
    simulations: int = 1000,
    seed: int = 42,
    concentration: float = 80.0,
) -> dict[str, float]:
    candidates = rank_trials(profile, trials)
    if not candidates:
        return {}
    keys = tuple(DEFAULT_WEIGHTS)
    base_weights = np.array([DEFAULT_WEIGHTS[key] for key in keys], dtype=float)
    matrix = np.array([
        [candidate.decision.components[key] for key in keys]
        for candidate in candidates
    ])
    rng = np.random.default_rng(seed)
    sampled_weights = rng.dirichlet(base_weights * concentration, size=simulations)
    scores = matrix @ sampled_weights.T
    selected = np.argsort(-scores, axis=0)[: min(top_k, len(candidates)), :]
    counts = np.bincount(selected.ravel(), minlength=len(candidates))
    return {
        candidate.trial.nct_id: float(count / simulations)
        for candidate, count in zip(candidates, counts)
    }

