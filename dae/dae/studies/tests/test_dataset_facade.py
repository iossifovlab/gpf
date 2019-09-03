def test_dataset_facade_simple(variants_db_fixture):
    assert sorted(variants_db_fixture.get_datasets_ids()) == \
        sorted([
            'quads_in_parent_ds', 'composite_dataset_ds', 'quads_in_child_ds',
            'quads_composite_ds', 'inheritance_trio_ds',
            'quads_two_families_ds', 'quads_variant_types_ds', 'quads_f1_ds',
            'quads_f2_ds'
        ])


def test_dataset_facade_get_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('quads_in_parent_ds')
    assert dataset is not None
    assert dataset.id == 'quads_in_parent_ds'


def test_dataset_facade_get_all_dataset_configs(variants_db_fixture):
    configs = variants_db_fixture.get_all_dataset_configs()
    assert len(configs) == 9


def test_dataset_facade_get_all_datasets(variants_db_fixture):
    datasets = variants_db_fixture.get_all_datasets()
    assert len(datasets) == 9
