from __future__ import annotations

import shutil
import json
from pathlib import Path

from neuronav.io import load_trials
from neuronav.models import PatientProfile
from neuronav.ranking import rank_trials


def main() -> None:
    assets = Path("docs/assets")
    assets.mkdir(parents=True, exist_ok=True)
    stems = ("figure1_navigation_performance", "figure2_trial_landscape")
    for stem in stems:
        for suffix in (".svg", ".png"):
            source = Path("figures") / f"{stem}{suffix}"
            if not source.exists():
                raise FileNotFoundError(f"Generate figures first: missing {source}")
            shutil.copy2(source, assets / source.name)

    # Export public, precomputed evidence for the static workflow explorer.
    report = json.loads(Path("results/sample_navigation_report.json").read_text(encoding="utf-8"))
    metadata = json.loads(Path("data/metadata.json").read_text(encoding="utf-8"))
    profile = PatientProfile(**report["profile"])
    screened = rank_trials(profile, load_trials("data/processed/trials_snapshot.csv"))
    demo = {
        "profile": report["profile"],
        "records": metadata["records"],
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "screened_candidates": len(screened),
        "audit_count": len(report["audits"]),
        "trace": report["trace"],
        "candidates": [],
    }
    for item in report["ranked_trials"][:3]:
        trial = item["trial"]
        expected_url = "https://clinicaltrials.gov/study/" + trial["nct_id"]
        if trial["source_url"] != expected_url:
            raise ValueError("Unexpected registry source URL in demo report")
        demo["candidates"].append({
            "nct_id": trial["nct_id"],
            "title": trial["title"],
            "overall_status": trial["overall_status"],
            "source_url": trial["source_url"],
            "rank": item["rank"],
            "base_score": item["decision"]["base_score"],
            "top_k_probability": item["top_k_probability"],
        })
    payload = json.dumps(demo, ensure_ascii=False, indent=2)
    (assets / "demo-data.js").write_text(
        "// Generated from the committed public snapshot and report.\n"
        "window.NEURONAV_DEMO = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"Prepared static project guide in {Path('docs/index.html').resolve()}")


if __name__ == "__main__":
    main()
