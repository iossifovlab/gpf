import pytest


pytestmark = pytest.mark.usefixtures("pheno_conf_path")


def test_dataset_facade_simple(dataset_facade):
    assert sorted(dataset_facade.get_all_dataset_ids()) == \
        sorted([
            'quads_in_parent_ds', 'composite_dataset_ds', 'quads_in_child_ds',
            'quads_composite_ds', 'inheritance_trio_ds',
            'quads_two_families_ds', 'quads_variant_types_ds', 'quads_f1_ds'
        ])


def test_dataset_facade_get_dataset(dataset_facade):
    dataset = dataset_facade.get_dataset('quads_in_parent_ds')
    assert dataset is not None
    assert dataset.id == 'quads_in_parent_ds'


def test_dataset_facade_get_all_dataset_configs(dataset_facade):
    configs = dataset_facade.get_all_dataset_configs()
    assert len(configs) == 8


def test_dataset_facade_get_all_datasets(dataset_facade):
    datasets = dataset_facade.get_all_datasets()
    assert len(datasets) == 8
