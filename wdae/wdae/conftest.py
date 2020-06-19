import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from users_api.models import WdaeUser

from gpf_instance.gpf_instance import reload_datasets, load_gpf_instance


pytest_plugins = ["dae_conftests.dae_conftests"]


@pytest.fixture()
def user(db):
    User = get_user_model()
    u = User.objects.create(
        email="user@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    u.set_password("secret")
    u.save()

    return u


@pytest.fixture()
def user_without_password(db):
    User = get_user_model()
    u = User.objects.create(
        email="user_without_password@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    u.save()

    return u


@pytest.fixture()
def admin(db):
    User = get_user_model()
    u = User.objects.create(
        email="admin@example.com",
        name="User",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    u.set_password("secret")
    u.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    u.groups.add(admin_group)

    return u


@pytest.fixture()
def user_client(user, client):
    client.login(email=user.email, password="secret")
    return client


@pytest.fixture()
def admin_client(admin, client):
    client.login(email=admin.email, password="secret")
    return client


@pytest.fixture(scope="function")
def wdae_gpf_instance(
    db, mocker, admin_client, fixtures_gpf_instance, gpf_instance_2013
):
    reload_datasets(fixtures_gpf_instance)
    mocker.patch(
        "query_base.query_base.get_gpf_instance",
        return_value=fixtures_gpf_instance,
    )
    mocker.patch(
        "gpf_instance.gpf_instance.get_gpf_instance",
        return_value=fixtures_gpf_instance,
    )
    mocker.patch(
        "gene_sets.expand_gene_set_decorator.get_gpf_instance",
        return_value=fixtures_gpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_gpf_instance",
        return_value=fixtures_gpf_instance,
    )

    return fixtures_gpf_instance


@pytest.fixture(scope="function")
def remote_settings(settings):
    settings.REMOTES = [{
        "id": "TEST_REMOTE",
        "host": "localhost",
        "base_url": "api/v3",
        "port": "21010",
        "user": "admin@iossifovlab.com",
        "password": "secret",
        }]

    # FIXME: Find a better workaround
    reload_datasets(load_gpf_instance())
