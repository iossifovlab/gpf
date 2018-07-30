def test_fixture_study_definition_is_loaded(study_definition):
    expected = {'test'}

    assert study_definition is not None
    studies = list(study_name for study_name in study_definition.configs)

    assert set(studies) == expected
