from __future__ import unicode_literals
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from users_api.models import WdaeUser


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run slow tests")
    parser.addoption("--runveryslow", action="store_true", default=False,
                     help="run very slow tests")
    parser.addoption("--ssc_wg", action="store_true", default=False,
                     help="run SSC WG tests")
    parser.addoption("--nomysql", action="store_true", default=False,
                     help="skip tests that require mysql")


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
def user(db, user_model):
    u = user_model.objects.create_user('user@example.com', 'secret123')
    u.save()

    return u


@pytest.fixture()
def admin_user(db, user_model):
    u = user_model.objects.create_superuser('admin@example.com', 'secret')
    u.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    any_dataset_group, _ = Group.objects.get_or_create(name='any_dataset')

    u.groups.add(admin_group)
    u.groups.add(any_dataset_group)

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password='secret123')
    return client


@pytest.fixture()
def admin_client(admin_user, client):
    client.login(email=admin_user.email, password='secret')
    return client
