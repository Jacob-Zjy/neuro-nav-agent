from __future__ import annotations

from dataclasses import replace

from .audit import audit_decision
from .models import AgentStep, NavigationReport, PatientProfile, RankedTrial, TrialRecord
from .ranking import rank_robustness, rank_trials


class NeuroNavAgent:
    """Hybrid navigator: tool orchestration with deterministic safety gates."""

    LIMITATIONS = (
        "The system checks only registered structured fields automatically.",
        "Free-text eligibility criteria require review by a trial coordinator.",
        "Rankings indicate navigation relevance, not medical benefit or eligibility.",
        "Only non-identifying research profiles should be entered.",
    )

    def navigate(
        self,
        profile: PatientProfile,
        trials: list[TrialRecord],
        top_k: int = 5,
        simulations: int = 1000,
        seed: int = 42,
    ) -> NavigationReport:
        ranked = rank_trials(profile, trials)
        trace = [
            AgentStep("profile_intake", "completed", "Accepted a minimal non-identifying profile."),
            AgentStep(
                "structured_screen",
                "completed",
                f"Evaluated {len(trials)} registry records; {len(ranked)} had no hard structured exclusion.",
            ),
        ]
        probabilities = rank_robustness(
            profile, trials, top_k=top_k, simulations=simulations, seed=seed
        )
        enriched: list[RankedTrial] = []
        audits = {}
        for candidate in ranked[:top_k]:
            enriched_candidate = replace(
                candidate,
                top_k_probability=probabilities.get(candidate.trial.nct_id, 0.0),
            )
            enriched.append(enriched_candidate)
            audits[candidate.trial.nct_id] = audit_decision(
                candidate.trial, candidate.decision
            )
        trace.extend([
            AgentStep(
                "sensitivity_analysis",
                "completed",
                f"Sampled {simulations} weight sets with seed {seed}.",
            ),
            AgentStep(
                "evidence_audit",
                "completed" if all(audit.passed for audit in audits.values()) else "attention",
                f"Audited {len(audits)} displayed candidates against registered source fields.",
            ),
            AgentStep(
                "report",
                "completed",
                "Returned navigation candidates with explicit unresolved criteria and human-review safeguards.",
            ),
        ])
        return NavigationReport(
            profile=profile,
            ranked_trials=tuple(enriched),
            audits=audits,
            trace=tuple(trace),
            limitations=self.LIMITATIONS,
        )
