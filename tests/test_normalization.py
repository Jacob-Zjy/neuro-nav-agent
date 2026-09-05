from neuronav.normalization import condition_similarity, normalize_country, parse_age_years


def test_parse_age_units_to_years():
    assert parse_age_years("18 Years") == 18
    assert parse_age_years("18 Months") == 1.5
    assert round(parse_age_years("52 Weeks"), 2) == 1.0
    assert parse_age_years(None) is None


def test_condition_aliases_and_country_aliases():
    assert condition_similarity("MCI", ("Mild Cognitive Impairment",)) == 1.0
    assert condition_similarity("Type 2 Diabetes", ("Alzheimer Disease",)) == 0.0
    assert normalize_country("USA") == "united states"

