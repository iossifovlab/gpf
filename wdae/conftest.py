import pytest
from django.contrib.auth import get_user_model
from datasets_api.models import Dataset


@pytest.fixture()
def user_model(db):
    return get_user_model()


@pytest.fixture()
def default_datasets(db):
    Dataset.recreate_dataset_perm('SD', [])
    Dataset.recreate_dataset_perm('SSC', [])
    Dataset.recreate_dataset_perm('VIP', [])


@pytest.fixture()
def user(user_model):
    u = user_model.objects.create_user('user@example.com', 'secret')
    u.save()

    return u


@pytest.fixture()
def admin_user(user_model):
    u = user_model.objects.create_superuser('admin@example.com', 'secret')
    u.save()

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password='secret')
    return client


@pytest.fixture()
def admin_client(db, admin_user, client):
    client.login(email=admin_user.email, password='secret')
    return client
