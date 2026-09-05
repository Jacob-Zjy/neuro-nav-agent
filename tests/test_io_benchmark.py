from neuronav.benchmark import generate_benchmark
from neuronav.io import load_trials, save_trials

from .test_eligibility import sample_trial


def test_trial_snapshot_roundtrip(tmp_path):
    path = tmp_path / "trials.csv"
    expected = [sample_trial()]
    save_trials(path, expected)
    assert load_trials(path) == expected


def test_benchmark_contains_positive_and_controlled_negative_cases():
    cases = generate_benchmark([sample_trial()], max_trials=1)
    assert any(case.expected_match for case in cases)
    assert any(not case.expected_match for case in cases)
    assert {case.perturbation for case in cases} >= {
        "none", "condition_mismatch", "no_registered_local_site"
    }
