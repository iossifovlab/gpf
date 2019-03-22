import pytest
from django.contrib.auth import get_user_model


@pytest.fixture()
def user(db):
    User = get_user_model()
    u = User.objects.create(
        email="user@example.com",
        name="User",
        is_staff=True,
        is_active=True,
        is_superuser=False)
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def admin(db):
    User = get_user_model()
    u = User.objects.create(
        email="user@example.com",
        name="User",
        is_staff=True,
        is_active=True,
        is_superuser=True)
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password="secret")
    return client


@pytest.fixture()
def admin_client(admin, client):
    client.login(email=admin.email, password="secret")
    return client
