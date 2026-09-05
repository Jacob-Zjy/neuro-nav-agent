from neuronav.audit import audit_decision
from neuronav.eligibility import assess_structured
from neuronav.models import PatientProfile, TrialRecord


def sample_trial(**overrides):
    values = dict(
        nct_id="NCT00000001",
        title="Cognitive intervention study",
        overall_status="RECRUITING",
        conditions=("Mild Cognitive Impairment",),
        sex="ALL",
        minimum_age_years=50,
        maximum_age_years=80,
        countries=("United States",),
        phases=("NA",),
        interventions=("Behavioral",),
        eligibility_text="Registered eligibility criteria.",
        source_url="https://clinicaltrials.gov/study/NCT00000001",
    )
    values.update(overrides)
    return TrialRecord(**values)


def test_potential_match_is_traced_and_audited():
    profile = PatientProfile("MCI", age=65, sex="female", country="USA")
    trial = sample_trial()
    decision = assess_structured(profile, trial)
    assert decision.status == "potential_match"
    assert decision.clinical_review_required
    assert audit_decision(trial, decision).passed


def test_hard_structured_exclusion_blocks_match():
    profile = PatientProfile("MCI", age=40, sex="female", country="USA")
    decision = assess_structured(profile, sample_trial())
    assert decision.status == "not_match"
    assert any("outside" in reason for reason in decision.unresolved)


def test_location_is_a_caution_not_clinical_exclusion():
    profile = PatientProfile("MCI", age=65, sex="female", country="China")
    decision = assess_structured(profile, sample_trial())
    assert decision.status == "potential_match"
    assert any(item.outcome == "caution" for item in decision.evidence)

