import os


def test_configs_is_read_properly(study_configs):
    assert study_configs is not None


def test_fixture_configs_have_correct_studies(study_configs):
    expected = {'test'}
    studies = list(study.study_name for study in study_configs)
    assert set(studies) == expected


def test_prefix_gets_default_location_as_config(study_configs):
    test_study_config = next(
        study for study in study_configs if study.study_name == 'test')

    assert test_study_config is not None

    assert os.path.isabs(test_study_config.prefix)

