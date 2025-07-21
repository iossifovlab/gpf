# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from datetime import timedelta
from typing import cast

import pytest
import pytest_mock
import yaml
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group
from django.test import Client
from django.utils import timezone
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from oauth2_provider.models import (
    AccessToken,
    Application,
    get_access_token_model,
    get_application_model,
)
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from users_api.models import WdaeUser
from utils.testing import setup_t4c8_instance

from federation.remote_extension import GPFRemoteExtension
from rest_client.rest_client import GPFOAuthSession, RESTClient


def build_remote_config() -> dict[str, str]:
    host = os.environ.get("TEST_REMOTE_HOST", "http://localhost:21010")
    return {
        "id": "TEST_REMOTE",
        "url": f"{host}",
        "client_id": "federation",
        "client_secret": "secret",
    }


@pytest.fixture
def rest_client() -> RESTClient:
    remote_config = build_remote_config()

    session = GPFOAuthSession(
        remote_config["url"],
        remote_config["client_id"],
        remote_config["client_secret"],
        f"{remote_config['url']}/login",
    )

    client = RESTClient(
        session,
        remote_config["client_id"],
    )

    assert client is not None

    return client


@pytest.fixture(scope="session")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    instance = setup_t4c8_instance(root_path)

    with open(instance.dae_config_path, "a") as f:
        f.write(yaml.dump({"remotes": [build_remote_config()]}))

    return WGPFInstance.build(instance.dae_config_path, grr=instance.grr)


@pytest.fixture(scope="session")
def test_remote_extension(
    t4c8_instance: WGPFInstance) -> GPFRemoteExtension:
    return t4c8_instance.extensions.get("remote_extension")


@pytest.fixture
def t4c8_wgpf_instance(
    t4c8_instance: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:

    query_transformer = QueryTransformer(
        t4c8_instance.gene_scores_db,
        t4c8_instance.reference_genome.chromosomes,
        t4c8_instance.reference_genome.chrom_prefix,
    )

    response_transformer = ResponseTransformer(
        t4c8_instance.gene_scores_db,
    )

    reload_datasets(t4c8_instance)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=t4c8_instance,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_query_transformer",
        return_value=query_transformer,
    )
    mocker.patch(
        "query_base.query_base.get_or_create_response_transformer",
        return_value=response_transformer,
    )
    mocker.patch(
        "utils.expand_gene_set.get_wgpf_instance",
        return_value=t4c8_instance,
    )

    return t4c8_instance


@pytest.fixture
def admin_client(
    admin: AbstractUser,  # noqa: ARG001
    tokens: tuple[AccessToken, AccessToken],  # noqa: ARG001
) -> Client:
    return Client(HTTP_AUTHORIZATION="Bearer admin-token")


@pytest.fixture
def admin(
    db: None,  # noqa: ARG001
) -> WdaeUser:
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="admin@example.com",
        name="Admin",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    new_user.set_password("secret")
    new_user.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    new_user.groups.add(admin_group)

    return cast(WdaeUser, new_user)  # type: ignore


@pytest.fixture
def tokens(
    admin: WdaeUser, user: WdaeUser, oauth_app: Application,
) -> tuple[AccessToken, AccessToken]:
    access_token = get_access_token_model()
    user_access_token = access_token(
        user=user,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="user-token",  # noqa: S106
        application=oauth_app,
    )
    admin_access_token = access_token(
        user=admin,
        scope="read write",
        expires=timezone.now() + timedelta(seconds=300),
        token="admin-token",  # noqa: S106
        application=oauth_app,
    )
    user_access_token.save()
    admin_access_token.save()
    return (
        cast(AccessToken, user_access_token),
        cast(AccessToken, admin_access_token),
    )


@pytest.fixture
def user(
    db: None,  # noqa: ARG001
) -> WdaeUser:
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

    return cast(WdaeUser, new_user)  # type: ignore


@pytest.fixture
def oauth_app(admin: AbstractUser) -> Application:
    application = get_application_model()
    new_application = application(
        name="testing client app",
        user_id=admin.id,  # type: ignore
        client_type="confidential",
        authorization_grant_type="authorization-code",
        redirect_uris="http://localhost:4200/datasets",
        client_id="admin",
        client_secret="secret",  # noqa: S106
    )
    new_application.save()
    return cast(Application, new_application)
