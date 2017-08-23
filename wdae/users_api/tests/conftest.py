import pytest
from django.contrib.auth import get_user_model
from datasets_api.models import Dataset


@pytest.fixture()
def default_datasets(db):
    Dataset.recreate_dataset_perm('SD', [])
    Dataset.recreate_dataset_perm('SSC', [])
    Dataset.recreate_dataset_perm('VIP', [])


@pytest.fixture()
def user(db):
    User = get_user_model()
    u = User.objects.create(
        email="user@example.com",
        name="First",
        is_staff=False,
        is_active=True,
        is_superuser=False)
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def admin(db):
    User = get_user_model()
    u = User.objects.create(
        email="admin@example.com",
        name="First",
        is_staff=True,
        is_active=True,
        is_superuser=True)
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def logged_user_client(user, client):
    client.login(email=user.email, password='secret')
    return client


@pytest.fixture()
def logged_admin_client(db, admin, client):
    client.login(email=admin.email, password='secret')
    return client
