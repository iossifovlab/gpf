def test_fixture_factory_can_be_loaded(study_factory):
    assert study_factory is not None


def test_factory_can_create_study_from_config(study_definition, study_factory):
    test_config = study_definition.get_study_config('quads_f1')

    assert study_factory.make_study(test_config) is not None
