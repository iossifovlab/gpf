import os

ALL_STUDIES = {'test', 'test_enabled_true', 'autism_and_epilepsy'}


def get_study(study_configs, study_name):
    return next(
        study for study in study_configs
        if study.study_name == study_name)


def test_configs_is_read_properly(study_configs):
    assert study_configs is not None


def test_fixture_configs_have_correct_studies(study_configs):
    studies = list(study.study_name for study in study_configs)
    assert set(studies) == ALL_STUDIES


def test_prefix_gets_default_location_as_config(study_configs):
    test_study_config = get_study(study_configs, 'test')

    assert test_study_config is not None

    assert os.path.isabs(test_study_config.prefix)


def test_enabled_option(study_configs):
    studies = set([study.study_name for study in study_configs])

    assert studies == ALL_STUDIES
    assert 'test_enabled_false' not in studies


def test_multiple_phenotypes_are_loaded(study_configs):
    study = get_study(study_configs, 'autism_and_epilepsy')
    print(study)

    assert study.phenotypes == {'autism', 'epilepsy'}
