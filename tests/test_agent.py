from neuronav.agent import NeuroNavAgent
from neuronav.models import PatientProfile

from .test_eligibility import sample_trial


def test_agent_ranks_only_potential_matches_and_is_reproducible():
    trials = [
        sample_trial(nct_id="NCT00000001"),
        sample_trial(nct_id="NCT00000002", countries=("China",)),
        sample_trial(nct_id="NCT00000003", overall_status="COMPLETED"),
    ]
    profile = PatientProfile("MCI", age=65, sex="female", country="China")
    agent = NeuroNavAgent()
    report_a = agent.navigate(profile, trials, top_k=2, simulations=100, seed=7)
    report_b = agent.navigate(profile, trials, top_k=2, simulations=100, seed=7)
    assert [item.trial.nct_id for item in report_a.ranked_trials] == [
        "NCT00000002", "NCT00000001"
    ]
    assert report_a.ranked_trials == report_b.ranked_trials
    assert all(audit.passed for audit in report_a.audits.values())
    assert [step.name for step in report_a.trace] == [
        "profile_intake", "structured_screen", "sensitivity_analysis",
        "evidence_audit", "report"
    ]
