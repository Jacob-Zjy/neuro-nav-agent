from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from .eligibility import RECRUITING_STATUSES
from .models import TrialRecord


def trial_landscape(trials: list[TrialRecord]) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame]:
    if not trials:
        raise ValueError("Trial landscape requires at least one trial.")
    status_counts = Counter(trial.overall_status for trial in trials)
    country_counts = Counter(country for trial in trials for country in trial.countries)
    total_country_mentions = sum(country_counts.values())
    shares = np.array(list(country_counts.values()), dtype=float) / max(total_country_mentions, 1)
    hhi = float(np.sum(shares ** 2)) if len(shares) else float("nan")
    recruiting = sum(trial.overall_status in RECRUITING_STATUSES for trial in trials)
    with_location = sum(bool(trial.countries) for trial in trials)
    multi_country = sum(len(trial.countries) > 1 for trial in trials)
    top_share = float(shares.max()) if len(shares) else float("nan")
    summary = {
        "n_trials": len(trials),
        "recruiting_share": recruiting / len(trials),
        "location_completeness": with_location / len(trials),
        "multi_country_share": multi_country / len(trials),
        "top_country_share": top_share,
        "country_hhi": hhi,
        "effective_country_count": 1 / hhi if hhi > 0 else float("nan"),
    }
    status_df = pd.DataFrame(status_counts.most_common(), columns=["status", "n_trials"])
    country_df = pd.DataFrame(country_counts.most_common(), columns=["country", "n_trial_locations"])
    return summary, status_df, country_df

