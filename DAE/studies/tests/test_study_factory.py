def test_fixture_factory_can_be_loaded(study_factory):
    assert study_factory is not None

    expected = {'test'}
    assert set(study_factory.get_dataset_names()) == expected


def test_factory_can_get_single_dataset(study_factory):
    test_dataset = study_factory.get_dataset('test')

    assert test_dataset is not None


def test_factory_can_get_all_datasets(study_factory):
    test_datasets = study_factory.get_all_datasets()

    assert test_datasets is not None
    assert len(test_datasets) == 1
