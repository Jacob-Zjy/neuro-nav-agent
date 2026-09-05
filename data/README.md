# Data provenance

`data/processed/trials_snapshot.csv` is generated from the public
[ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/about-api). It
contains study-registration metadata and no participant-level health records.
The default pipeline follows every API page for the three query terms and keeps
currently open recruitment statuses. It therefore avoids treating an arbitrary
first page as a representative epidemiological sample.

`data/benchmark/cases.jsonl` contains explicitly synthetic, non-identifying
profiles derived from structured registry fields. Controlled perturbations
(condition, age, sex, or registered-site country) create auditable positive and
negative pre-screening cases. Here, a positive case means a locally actionable
structured match. The benchmark tests structured navigation logic only; it must not be
interpreted as validation of full clinical eligibility or health outcomes.

Recreate both datasets:

```bash
python -m scripts.download_trials
python -m scripts.build_benchmark
```

The retrieval timestamp, query terms, sample counts, and construction rules are
stored in adjacent metadata files.
