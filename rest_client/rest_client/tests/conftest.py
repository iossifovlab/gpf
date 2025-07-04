# pylint: disable=W0621,C0114,C0116,W0212,W0613
from urllib.parse import urlparse

import pytest

from rest_client.mailhog_client import MailhogClient
from rest_client.rest_client import (
    GPFOAuthSession,
    GPFPasswordSession,
    RESTClient,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--url",
        dest="url",
        action="store",
        default="http://localhost:8000",
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
    res = request.config.getoption("--url")
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
    res = request.config.getoption("--mailhog")
    parsed = urlparse(res)
    if not parsed.scheme:
        res = f"http://{res}"
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid URL: {res}")
    parsed = urlparse(res)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


@pytest.fixture
def oauth_admin() -> RESTClient:
    confidential_session = GPFOAuthSession(
        base_url="http://resttest:21011",
        client_id="resttest1",
        client_secret="secret",  # noqa: S106
        redirect_uri="http://resttest:21011/login",
    )

    client = RESTClient(confidential_session)
    client.login()
    return client


@pytest.fixture(
    params=["basic", "oauth2_confidential_client"],
)
def admin_client(
    request: pytest.FixtureRequest,
) -> RESTClient:
    if request.param == "basic":
        basic_session = GPFPasswordSession(
            base_url="http://resttest:21011",
            username="admin@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFOAuthSession(
            base_url="http://resttest:21011",
            client_id="resttest1",
            client_secret="secret",  # noqa: S106
            redirect_uri="http://resttest:21011/login",
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
) -> RESTClient:
    if request.param == "basic":
        basic_session = GPFPasswordSession(
            base_url="http://resttest:21011",
            username="research@iossifovlab.com",
            password="secret",  # noqa: S106
        )
        client = RESTClient(basic_session)
        client.login()
        return client

    if request.param == "oauth2_confidential_client":
        confidential_session = GPFOAuthSession(
            base_url="http://resttest:21011",
            client_id="resttest2",
            client_secret="secret",  # noqa: S106
            redirect_uri="http://resttest:21011/login",
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
def annon_client() -> RESTClient:
    """REST client fixture."""
    session = GPFPasswordSession(
        "http://resttest:21011",
        "annonymous@iossifovlab.com",
        "secret",
        )
    return RESTClient(session)
