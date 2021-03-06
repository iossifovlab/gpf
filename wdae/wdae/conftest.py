import pytest
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from users_api.models import WdaeUser

from remote.rest_api_client import RESTClient

from dae.gpf_instance.gpf_instance import cached
from gpf_instance.gpf_instance import WGPFInstance,\
    reload_datasets, load_gpf_instance
from dae.genome.genomes_db import GenomesDB


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


@pytest.fixture(scope="session")
def wgpf_instance(default_dae_config):
    class GenomesDbInternal(GenomesDB):
        def get_default_gene_models_id(self, genome_id=None):
            return "RefSeq2013"

    class WGPFInstanceInternal(WGPFInstance):
        @property
        @cached
        def genomes_db(self):
            return GenomesDbInternal(
                default_dae_config.dae_data_dir,
                default_dae_config.genomes_db.conf_file,
            )

    def build(work_dir=None, load_eagerly=False):
        return WGPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly
        )

    return build


@pytest.fixture(scope="session")
def fixtures_wgpf_instance(wgpf_instance, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)


@pytest.fixture(scope="function")
def wdae_gpf_instance(
        db, mocker, admin_client, fixtures_wgpf_instance):

    reload_datasets(fixtures_wgpf_instance)
    mocker.patch(
        "query_base.query_base.get_gpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "gpf_instance.gpf_instance.get_gpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "gene_sets.expand_gene_set_decorator.get_gpf_instance",
        return_value=fixtures_wgpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_gpf_instance",
        return_value=fixtures_wgpf_instance,
    )

    return fixtures_wgpf_instance


@pytest.fixture(scope="function")
def remote_settings(settings):
    host = os.environ.get("TEST_REMOTE_HOST", "localhost")
    remote = {
        "id": "TEST_REMOTE",
        "host": host,
        "base_url": "api/v3",
        "port": "21010",
        "user": "admin@iossifovlab.com",
        "password": "secret",
    }
    settings.REMOTES = [remote]

    # FIXME: Find a better workaround
    reload_datasets(load_gpf_instance())

    return remote

@pytest.fixture(scope="function")
def rest_client(admin_client, remote_settings):
    client = RESTClient(
        remote_settings["id"],
        remote_settings["host"],
        remote_settings["user"],
        remote_settings["password"],
        base_url=remote_settings["base_url"],
        port=remote_settings["port"]
    )

    assert client.session is not None, \
        "Failed to create session for REST client"

    return client
