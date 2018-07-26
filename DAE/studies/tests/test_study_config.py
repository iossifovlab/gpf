def test_configs_is_read_properly(study_configs):
    assert study_configs is not None


def test_fixture_configs_have_correct_studies(study_configs):
    expected = {'test'}
    studies = list(study.study_name for study in study_configs)
    assert set(studies) == expected


def test_fixture_study_definition_is_loaded(study_definition):
    expected = {'test'}

    assert study_definition is not None
    studies = list(study_name for study_name in study_definition.configs)

    assert set(studies) == expected
