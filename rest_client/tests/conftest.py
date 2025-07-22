# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0412
from typing import cast
from urllib.parse import urlparse

import pytest
import yaml
from gpf_instance.gpf_instance import WGPFInstance
from rest_client.mailhog_client import MailhogClient
from utils.testing import setup_t4c8_instance

from rest_client.rest_client import (
    GPFAnonymousSession,
    GPFOAuthSession,
    GPFPasswordSession,
    RESTClient,
)


def build_remote_config(base_url: str) -> dict[str, str]:
    host = base_url
    return {
        "id": "TEST_REMOTE",
        "url": host,
        "client_id": "federation",
        "client_secret": "secret",
    }


def build_remote_config_user(base_url: str) -> dict[str, str]:
    host = base_url
    return {
        "id": "TEST_REMOTE",
        "url": host,
        "client_id": "federation2",
        "client_secret": "secret",
    }


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--url",
        dest="url",
        action="store",
        default="http://localhost:21010",
        help="REST API URL",
    )

    parser.addoption(
        "--mailhog",
        dest="mailhog",
        action="store",
        default="http://localhost:8025",
        help="Mailhog REST API URL",
    )


@pytest.fixture
def base_url(request: pytest.FixtureRequest) -> str:
    res = cast(str, request.config.getoption("--url"))
    parsed = urlparse(res)
    if not parsed.scheme:
        res = f"http://{res}"
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid URL: {res}")
    parsed = urlparse(res)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


@pytest.fixture
def mailhog_url(request: pytest.FixtureRequest) -> str:
    res = cast(str, request.config.getoption("--mailhog"))
    parsed = urlparse(res)
    if not parsed.scheme:
        res = f"http://{res}"
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid URL: {res}")
    parsed = urlparse(res)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


@pytest.fixture
def oauth_admin(base_url: str) -> RESTClient:
    conf = build_remote_config(base_url)
    confidential_session = GPFOAuthSession(
            base_url=conf["url"],
            client_id=conf["client_id"],
            client_secret=conf["client_secret"],
            redirect_uri=f"{conf['url']}/login",
    )

    client = RESTClient(confidential_session)
    client.login()
    return client


@pytest.fixture(
    params=["basic", "oauth2_confidential_client"],
)
def admin_client(
    request: pytest.FixtureRequest,
    base_url: str,
) -> RESTClient:
    conf = build_remote_config(base_url)
    if request.param == "basic":
        basic_session = GPFPasswordSession(
            base_url=conf["url"],
            username="admin@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFOAuthSession(
            base_url=conf["url"],
            client_id=conf["client_id"],
            client_secret=conf["client_secret"],
            redirect_uri=f"{conf['url']}/login",
        )

        client = RESTClient(confidential_session)
        client.login()
        return client
    raise ValueError(f"Unknown request parameter: {request.param}")


@pytest.fixture(
    params=["basic", "oauth2_confidential_client"],
)
def user_client(
    request: pytest.FixtureRequest,
    base_url: str,
) -> RESTClient:
    conf = build_remote_config_user(base_url)
    if request.param == "basic":
        basic_session = GPFPasswordSession(
            base_url=conf["url"],
            username="research@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFOAuthSession(
            base_url=conf["url"],
            client_id=conf["client_id"],
            client_secret=conf["client_secret"],
            redirect_uri=f"{conf['url']}/login",
        )

        client = RESTClient(confidential_session)
        client.login()
        return client

    raise ValueError(f"Unknown request parameter: {request.param}")


@pytest.fixture
def mail_client(mailhog_url: str) -> MailhogClient:
    """REST client fixture."""
    return MailhogClient(mailhog_url)


@pytest.fixture
def anon_client(base_url: str) -> RESTClient:
    """REST client fixture."""
    conf = build_remote_config(base_url)
    session = GPFAnonymousSession(conf["url"])
    return RESTClient(session)


@pytest.fixture
def rest_client(base_url: str) -> RESTClient:
    remote_config = build_remote_config(base_url)
    session = GPFOAuthSession(
        base_url=remote_config["url"],
        client_id=remote_config["client_id"],
        client_secret=remote_config["client_secret"],
        redirect_uri=f"{remote_config['url']}/login",
    )
    client = RESTClient(
        session, remote_config["id"],
    )
    client.login()
    assert session.token is not None, \
        "Failed to get auth token for REST client"
    return client


@pytest.fixture(scope="session")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    base_url: str,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_instance")
    instance = setup_t4c8_instance(root_path)

    with open(instance.dae_config_path, "a") as f:
        f.write(yaml.dump({"remotes": [build_remote_config(base_url)]}))

    return WGPFInstance.build(instance.dae_config_path, grr=instance.grr)
