def test_inheritance_trio_can_init(inheritance_trio_wrapper):
    assert inheritance_trio_wrapper is not None


def test_dataset_facade_works(dataset_facade):
    assert dataset_facade is not None

    assert len(dataset_facade.get_all_datasets()) > 0
