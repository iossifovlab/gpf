def test_fixture_factory_can_be_loaded(study_factory):
    assert study_factory is not None

    expected = {'test'}
    assert set(study_factory.get_study_names()) == expected


def test_factory_can_get_single_study(study_factory):
    test_study = study_factory.get_study('test')

    assert test_study is not None


def test_factory_can_get_all_studies(study_factory):
    test_studies = study_factory.get_all_studies()

    assert test_studies is not None
    assert len(test_studies) == 1
