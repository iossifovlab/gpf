

def test_dataset_facade_simple(dataset_facade):
    assert dataset_facade.get_all_dataset_ids() == \
        [
            'quads_in_parent', 'composite_dataset', 'quads_in_child',
            'quads_composite', 'inheritance_trio', 'quads_two_families',
            'quads_variant_types', 'quads_f1'
        ]


def test_dataset_facade_get_dataset(dataset_facade):
    dataset = dataset_facade.get_dataset('quads_in_parent')
    assert dataset is not None
    assert dataset.id == 'quads_in_parent'


def test_dataset_facade_get_all_dataset_configs(dataset_facade):
    configs = dataset_facade.get_all_dataset_configs()
    assert len(configs) == 8
