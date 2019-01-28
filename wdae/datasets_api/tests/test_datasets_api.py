import pytest


@pytest.mark.django_db(transaction=True)
def test_datasets_api_get_all(recreate_dataset_perm, dataset_view, user):
    datasets = dataset_view.get(user).data['data']
    assert datasets
    assert len(datasets) == 8


@pytest.mark.django_db(transaction=True)
def test_datasets_api_get_one(recreate_dataset_perm, dataset_view, user):
    dataset = dataset_view.get(user, 'quads_in_parent').data['data']
    assert dataset
    assert dataset['name'] == 'QUADS_IN_PARENT'
