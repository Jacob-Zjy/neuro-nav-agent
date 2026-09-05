// Generated from the committed public snapshot and report.
window.NEURONAV_DEMO = {
  "profile": {
    "condition": "Mild Cognitive Impairment",
    "age": 65,
    "sex": "female",
    "country": "Brazil",
    "preferences": []
  },
  "records": 1968,
  "retrieved_at_utc": "2026-09-05T03:46:19.903395+00:00",
  "screened_candidates": 1560,
  "audit_count": 10,
  "trace": [
    {
      "name": "profile_intake",
      "status": "completed",
      "detail": "Accepted a minimal non-identifying profile."
    },
    {
      "name": "structured_screen",
      "status": "completed",
      "detail": "Evaluated 1968 registry records; 1560 had no hard structured exclusion."
    },
    {
      "name": "sensitivity_analysis",
      "status": "completed",
      "detail": "Sampled 2000 weight sets with seed 42."
    },
    {
      "name": "evidence_audit",
      "status": "completed",
      "detail": "Audited 10 displayed candidates against registered source fields."
    },
    {
      "name": "report",
      "status": "completed",
      "detail": "Returned navigation candidates with explicit unresolved criteria and human-review safeguards."
    }
  ],
  "candidates": [
    {
      "nct_id": "NCT03263247",
      "title": "Cognitive Training in Patients With MCI Using fMRI",
      "overall_status": "ACTIVE_NOT_RECRUITING",
      "source_url": "https://clinicaltrials.gov/study/NCT03263247",
      "rank": 1,
      "base_score": 1.0,
      "top_k_probability": 1.0
    },
    {
      "nct_id": "NCT06733714",
      "title": "Association of Transcranial Alternating Current Stimulation with Digital Cognitive Training for Cognitive Remediation in Older Adults",
      "overall_status": "RECRUITING",
      "source_url": "https://clinicaltrials.gov/study/NCT06733714",
      "rank": 2,
      "base_score": 0.9875,
      "top_k_probability": 1.0
    },
    {
      "nct_id": "NCT07213700",
      "title": "InRAD Observational Study",
      "overall_status": "RECRUITING",
      "source_url": "https://clinicaltrials.gov/study/NCT07213700",
      "rank": 3,
      "base_score": 0.9625,
      "top_k_probability": 0.915
    }
  ]
};
