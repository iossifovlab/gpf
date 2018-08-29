import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from users_api.models import WdaeUser


@pytest.fixture()
def user_model():
    return get_user_model()


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def default_datasets():
    Dataset.recreate_dataset_perm('SD_TEST', [])
    Dataset.recreate_dataset_perm('SSC', [])
    Dataset.recreate_dataset_perm('SVIP', [])


@pytest.fixture()
def user(user_model):
    u = user_model.objects.create_user('user@example.com', 'secret123')
    u.save()

    return u


@pytest.fixture()
def admin_user(user_model):
    u = user_model.objects.create_superuser('admin@example.com', 'secret')
    u.save()
    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    u.groups.add(admin_group)

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password='secret123')
    return client


@pytest.fixture()
def admin_client(admin_user, client):
    client.login(email=admin_user.email, password='secret')
    return client
