from __future__ import annotations

import argparse
from collections import Counter

from neuronav.benchmark import generate_benchmark, save_benchmark
from neuronav.io import load_trials, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", default="data/processed/trials_snapshot.csv")
    parser.add_argument("--output", default="data/benchmark/cases.jsonl")
    parser.add_argument("--metadata", default="data/benchmark/metadata.json")
    parser.add_argument("--max-trials", type=int, default=120)
    args = parser.parse_args()

    cases = generate_benchmark(load_trials(args.trials), max_trials=args.max_trials)
    save_benchmark(args.output, cases)
    counts = Counter(case.perturbation for case in cases)
    write_json(args.metadata, {
        "n_cases": len(cases),
        "class_counts": Counter(str(case.expected_match) for case in cases),
        "perturbation_counts": counts,
        "construction": "Synthetic profiles derived from public structured trial fields.",
        "claim_boundary": "Evaluates structured pre-screening only, not full clinical eligibility.",
    })
    print(f"Saved {len(cases)} benchmark cases to {args.output}")


if __name__ == "__main__":
    main()

