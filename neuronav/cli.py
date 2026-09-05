from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .agent import NeuroNavAgent
from .io import load_trials, to_jsonable
from .models import PatientProfile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Navigate cognitive-health clinical trials.")
    parser.add_argument("--data", default="data/processed/trials_snapshot.csv")
    parser.add_argument("--condition", required=True)
    parser.add_argument("--age", type=float)
    parser.add_argument("--sex", choices=["female", "male"])
    parser.add_argument("--country")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--simulations", type=int, default=1000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    profile = PatientProfile(args.condition, args.age, args.sex, args.country)
    report = NeuroNavAgent().navigate(
        profile, load_trials(args.data), top_k=args.top_k, simulations=args.simulations
    )
    print(json.dumps(to_jsonable(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

