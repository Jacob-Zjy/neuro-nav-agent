from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PatientProfile:
    """Minimal, non-identifying information used for research matching."""

    condition: str
    age: float | None = None
    sex: str | None = None
    country: str | None = None
    preferences: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrialRecord:
    nct_id: str
    title: str
    overall_status: str
    conditions: tuple[str, ...]
    sex: str = "ALL"
    minimum_age_years: float | None = None
    maximum_age_years: float | None = None
    countries: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()
    interventions: tuple[str, ...] = ()
    eligibility_text: str = ""
    brief_summary: str = ""
    last_update: str = ""
    source_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceItem:
    check: str
    outcome: str
    explanation: str
    source_fields: tuple[str, ...]


@dataclass(frozen=True)
class MatchDecision:
    nct_id: str
    status: str
    base_score: float
    components: dict[str, float]
    evidence: tuple[EvidenceItem, ...]
    unresolved: tuple[str, ...] = ()
    clinical_review_required: bool = True


@dataclass(frozen=True)
class RankedTrial:
    trial: TrialRecord
    decision: MatchDecision
    rank: int
    top_k_probability: float = 0.0


@dataclass(frozen=True)
class AuditResult:
    passed: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentStep:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class NavigationReport:
    profile: PatientProfile
    ranked_trials: tuple[RankedTrial, ...]
    audits: dict[str, AuditResult]
    trace: tuple[AgentStep, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
