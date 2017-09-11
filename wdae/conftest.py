import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datasets_api.models import Dataset


@pytest.fixture()
def user_model():
    return get_user_model()


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def default_datasets(db):
    Dataset.recreate_dataset_perm('SD', [])
    Dataset.recreate_dataset_perm('SSC', [])
    Dataset.recreate_dataset_perm('VIP', [])


@pytest.fixture()
def user(db, user_model):
    u = user_model.objects.create_user('user@example.com', 'secret123')
    u.save()

    return u


@pytest.fixture()
def admin_user(db, user_model):
    u = user_model.objects.create_superuser('admin@example.com', 'secret')
    u.save()

    return u


@pytest.fixture()
def user_client(user, client):
    print("setup user client:", user, client)
    print(user.email)
    client.login(email=user.email, password='secret123')
    return client


@pytest.fixture()
def admin_client(db, admin_user, client):
    client.login(email=admin_user.email, password='secret')
    return client
