from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from neuronav.clinical_trials import API_URL, ClinicalTrialsClient
from neuronav.io import save_trials, write_json


DEFAULT_TERMS = ("Mild Cognitive Impairment", "Alzheimer Disease", "Dementia")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/processed/trials_snapshot.csv")
    parser.add_argument("--metadata", default="data/metadata.json")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--terms", nargs="+", default=list(DEFAULT_TERMS))
    args = parser.parse_args()

    trials = ClinicalTrialsClient().search_many(
        args.terms, page_size=args.page_size, open_only=not args.include_closed
    )
    save_trials(args.output, trials)
    write_json(args.metadata, {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": API_URL,
        "query_terms": args.terms,
        "records": len(trials),
        "scope": "all API pages for currently open recruitment statuses"
        if not args.include_closed else "all API pages across all recruitment statuses",
        "pagination_complete": True,
        "contains_personal_health_information": False,
        "note": "Public study-registration records; no participant-level data.",
    })
    print(f"Saved {len(trials)} unique trial records to {Path(args.output)}")


if __name__ == "__main__":
    main()
