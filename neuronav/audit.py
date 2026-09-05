from __future__ import annotations

from .models import AuditResult, MatchDecision, TrialRecord


ALLOWED_SOURCE_FIELDS = {
    "overall_status", "conditions", "minimum_age_years", "maximum_age_years",
    "sex", "countries", "phases", "interventions", "eligibility_text",
    "brief_summary", "last_update", "source_url",
}


def audit_decision(trial: TrialRecord, decision: MatchDecision) -> AuditResult:
    issues: list[str] = []
    if decision.nct_id != trial.nct_id:
        issues.append("Decision identifier does not match the source trial.")
    if not 0.0 <= decision.base_score <= 1.0:
        issues.append("Score is outside [0, 1].")
    if not decision.clinical_review_required:
        issues.append("Clinical review safeguard is missing.")
    if not decision.evidence:
        issues.append("No evidence trace was produced.")
    for item in decision.evidence:
        unknown = set(item.source_fields) - ALLOWED_SOURCE_FIELDS
        if unknown:
            issues.append(f"Unsupported evidence fields: {sorted(unknown)}")
    return AuditResult(passed=not issues, issues=tuple(issues))

