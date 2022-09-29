# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import logging
from datetime import timedelta

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.utils import timezone
from oauth2_provider.models import \
    get_access_token_model, get_application_model
from remote.rest_api_client import RESTClient

from gpf_instance.gpf_instance import WGPFInstance, get_gpf_instance,\
    reload_datasets, load_gpf_instance

from users_api.models import WdaeUser
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.group_repository import GenomicResourceGroupRepo
from dae.tools import generate_common_report

logger = logging.getLogger(__name__)

pytest_plugins = ["dae_conftests.dae_conftests"]


@pytest.fixture()
def user(db):
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="user@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    new_user.set_password("secret")
    new_user.save()

    return new_user


@pytest.fixture()
def user_without_password(db):
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="user_without_password@example.com",
        name="User",
        is_staff=False,
        is_active=True,
        is_superuser=False,
    )
    new_user.save()

    return new_user


@pytest.fixture()
def admin(db):
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="admin@example.com",
        name="User",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    new_user.set_password("secret")
    new_user.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    new_user.groups.add(admin_group)

    return new_user


@pytest.fixture()
def oauth_app(admin):
    application = get_application_model()
    new_application = application(**{
        "name": "testing client app",
        "user_id": admin.id,
        "client_type": "confidential",
        "authorization_grant_type": "authorization-code",
        "redirect_uris": "http://localhost:4200/datasets",
        "client_id": "admin",
        "client_secret": "secret"
    })
    new_application.save()
    return new_application


@pytest.fixture()
def tokens(admin, user, oauth_app):
    access_token = get_access_token_model()
    user_access_token = access_token(
        user=user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="user-token",
        application=oauth_app
    )
    admin_access_token = access_token(
        user=admin,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="admin-token",
        application=oauth_app
    )
    user_access_token.save()
    admin_access_token.save()
    return user_access_token, admin_access_token


@pytest.fixture()
def user_client(user, tokens):
    client = Client(HTTP_AUTHORIZATION="Bearer user-token")
    return client


@pytest.fixture()
def anonymous_client(client, db):
    client.logout()
    return client


@pytest.fixture()
def admin_client(admin, tokens):
    client = Client(HTTP_AUTHORIZATION="Bearer admin-token")
    return client


@pytest.fixture
def datasets(db):
    reload_datasets(get_gpf_instance())


@pytest.fixture(scope="session")
def wgpf_instance(default_dae_config, fixture_dirname):

    class WGPFInstanceInternal(WGPFInstance):
        pass

    def build(work_dir=None, load_eagerly=False):
        repositories = [
            build_genomic_resource_repository(
                {
                    "id": "grr_test_repo",
                    "type": "directory",
                    "directory": fixture_dirname("test_repo"),
                }
            ),
            build_genomic_resource_repository(
                {
                    "id": "fixtures",
                    "type": "directory",
                    "directory": fixture_dirname("genomic_resources")
                }),
            build_genomic_resource_repository(),
        ]
        grr = GenomicResourceGroupRepo(repositories)

        result = WGPFInstanceInternal(
            work_dir=work_dir, load_eagerly=load_eagerly, grr=grr
        )

        remote_host = os.environ.get("TEST_REMOTE_HOST", "localhost")
        if result.dae_config.remotes[0].id == "TEST_REMOTE":
            result.dae_config.remotes[0].host = remote_host
        result.load_remotes()

        return result

    return build


# @pytest.fixture(autouse=True)
# def switch_to_local_dae_db_dir(settings):
#     if getattr(settings, "TESTING", None):
#         print(100 * "+")
#         logger.error("testing environment...")
#         print(100 * "+")


@pytest.fixture(scope="session")
def fixtures_wgpf_instance(wgpf_instance, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)


@pytest.fixture(scope="function")
def wdae_gpf_instance(
    db, mocker, admin_client, fixtures_wgpf_instance, fixture_dirname
):
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
    wdae_gpf_instance.__autism_gene_profile_config = None

    return fixtures_wgpf_instance


@pytest.fixture(scope="function")
def wdae_gpf_instance_agp(  # pylint: disable=too-many-arguments
        db, mocker, admin_client, wgpf_instance, sample_agp,
        global_dae_fixtures_dir, agp_config, temp_filename,
        fixture_dirname):

    wdae_gpf_instance = wgpf_instance(global_dae_fixtures_dir)

    reload_datasets(wdae_gpf_instance)
    mocker.patch(
        "query_base.query_base.get_gpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "gpf_instance.gpf_instance.get_gpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "gene_sets.expand_gene_set_decorator.get_gpf_instance",
        return_value=wdae_gpf_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_gpf_instance",
        return_value=wdae_gpf_instance,
    )

    wdae_gpf_instance.__autism_gene_profile_config = agp_config
    main_gene_sets = {
        "CHD8 target genes",
        "FMRP Darnell",
        "FMRP Tuschl",
        "PSD",
        "autism candidates from Iossifov PNAS 2015",
        "autism candidates from Sanders Neuron 2015",
        "brain critical genes",
        "brain embryonically expressed",
        "chromatin modifiers",
        "essential genes",
        "non-essential genes",
        "postsynaptic inhibition",
        "synaptic clefts excitatory",
        "synaptic clefts inhibitory",
        "topotecan downreg genes"
    }
    mocker.patch.object(
        wdae_gpf_instance.gene_sets_db,
        "get_gene_set_ids",
        return_value=main_gene_sets
    )
    wdae_gpf_instance.__autism_gene_profile_db = \
        AutismGeneProfileDB(
            agp_config,
            os.path.join(wdae_gpf_instance.dae_db_dir, temp_filename),
            clear=True
        )
    wdae_gpf_instance._autism_gene_profile_db.insert_agp(sample_agp)

    yield wdae_gpf_instance

    wdae_gpf_instance.__autism_gene_profile_config = None
    wdae_gpf_instance.__autism_gene_profile_db = None


@pytest.fixture(scope="function")
def remote_config():
    host = os.environ.get("TEST_REMOTE_HOST", "localhost")
    remote = {
        "id": "TEST_REMOTE",
        "host": host,
        "base_url": "api/v3",
        "port": "21010",
        "credentials": "ZmVkZXJhdGlvbjpzZWNyZXQ=",
    }
    reload_datasets(load_gpf_instance())

    return remote


@pytest.fixture(scope="function")
def rest_client(admin_client, remote_config):
    client = RESTClient(
        remote_config["id"],
        remote_config["host"],
        remote_config["credentials"],
        base_url=remote_config["base_url"],
        port=remote_config["port"]
    )

    assert client.token is not None, \
        "Failed to get auth token for REST client"

    return client


@pytest.fixture(scope="function")
def use_common_reports(wdae_gpf_instance):
    all_configs = wdae_gpf_instance.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    args = ["--studies", "Study1,study4"]

    generate_common_report.main(args, wdae_gpf_instance)

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
