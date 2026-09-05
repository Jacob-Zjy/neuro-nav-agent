from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from neuronav.agent import NeuroNavAgent
from neuronav.analytics import trial_landscape
from neuronav.io import load_trials, write_json
from neuronav.models import PatientProfile
from neuronav.ranking import rank_robustness, rank_trials


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", default="data/processed/trials_snapshot.csv")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    trials = load_trials(args.trials)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary, statuses, countries = trial_landscape(trials)
    write_json(output / "landscape_summary.json", summary)
    statuses.to_csv(output / "status_counts.csv", index=False)
    countries.to_csv(output / "country_counts.csv", index=False)

    profile = PatientProfile("Mild Cognitive Impairment", 65, "female", "Brazil")
    report = NeuroNavAgent().navigate(profile, trials, top_k=10, simulations=2000, seed=42)
    write_json(output / "sample_navigation_report.json", report)
    ranked_all = rank_trials(profile, trials)
    probabilities = rank_robustness(profile, trials, top_k=10, simulations=2000, seed=42)
    robustness_rows = [
        {
            "rank": item.rank,
            "nct_id": item.trial.nct_id,
            "title": item.trial.title,
            "base_score": item.decision.base_score,
            "top_10_probability": probabilities.get(item.trial.nct_id, 0.0),
            "countries": "; ".join(item.trial.countries),
        }
        for item in ranked_all
    ]
    pd.DataFrame(robustness_rows).sort_values(
        ["top_10_probability", "base_score", "rank"], ascending=[False, False, True]
    ).head(10).to_csv(output / "rank_robustness.csv", index=False)
    print(pd.Series(summary).round(3).to_string())


if __name__ == "__main__":
    main()
