# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import re
from datetime import timedelta
from typing import Tuple

from rest_framework import status
from django.utils import timezone
from django.test.client import Client
from oauth2_provider.models import AccessToken

from users_api.models import WdaeUser, LOCKOUT_THRESHOLD
from users_api.models import AuthenticationLog, ResetPasswordCode


def lockout_email(client: Client, email: str) -> None:
    data = {
        "username": email,
        "password": "invalidpasswordinvalidpassword",
    }
    for _ in range(0, LOCKOUT_THRESHOLD + 1):
        client.post(
            "/accounts/login",
            json.dumps(data),
            content_type="application/json", format="json"
        )


def expire_email_lockout(email: str) -> None:
    """Wind back times of all logins so that the lockout expires."""
    query = AuthenticationLog.objects.filter(
        email__iexact=email
    ).order_by("-time", "-failed_attempt")
    last_login = AuthenticationLog.get_last_login_for(email)
    assert last_login is not None

    subtract_time = timedelta(
        seconds=pow(2, last_login.failed_attempt + 1 - LOCKOUT_THRESHOLD) * 60
    )
    for login in query:
        login.time = login.time - subtract_time
        login.save()


def test_successful_auth(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "http://localhost:4200/datasets"  # type: ignore


def test_successful_auth_with_next(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
        "next": "somewhere.com"
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "somewhere.com"  # type: ignore


def test_successful_auth_case_insensitive(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {
        "username": "UsER@ExAmPlE.cOm",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == "http://localhost:4200/datasets"  # type: ignore


def test_failed_auth(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {"username": "bad@example.com", "password": "secret"}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_no_username_auth(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {"username": "", "password": "secret"}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_user_info_after_auth(user_client: Client) -> None:
    response = user_client.get("/api/v3/users/get_user_info")
    data = response.json()
    assert data["loggedIn"] is True
    assert data["email"] == "user@example.com"


def test_no_password_auth(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.content.find(b"Password not provided") != -1


def test_email_auth_unsuccessful(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    """Try to login with a non-existing email."""
    url = "/accounts/login"
    data = {
        "username": "nonexistntuser@example.com",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_failed_auth_attempts(
    db: None, user: WdaeUser, client: Client,
    tokens: Tuple[AccessToken, AccessToken]
) -> None:
    # Check if the user is allowed four failed
    # login attempts before being locked out.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    for i in range(0, LOCKOUT_THRESHOLD):
        response = client.post(
            url, json.dumps(data),
            content_type="application/json", format="json"
        )
        last_login = AuthenticationLog.get_last_login_for(data["username"])
        assert last_login is not None

        assert last_login.failed_attempt == i + 1
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.content.find(b"Invalid login credentials") != -1

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert last_login is not None

    assert last_login.failed_attempt == LOCKOUT_THRESHOLD + 1
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content.find(b"This account is locked out") != -1


def test_failed_auth_lockouts(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    # Check if progressive lockouts are working.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    lockout_email(client, data["username"])

    for i in range(1, 5):
        response = client.post(
            url, json.dumps(data),
            content_type="application/json", format="json"
        )
        assert response.content.find(b"This account is locked out for") != -1
        regex = r"locked out for (\d+) hours and (\d+) minutes"
        match = re.search(regex, response.content.decode())
        assert match is not None

        response_hours, response_minutes = \
            map(int, match.groups())
        response_td = timedelta(
            hours=response_hours, minutes=response_minutes
        )
        expected_td = timedelta(minutes=pow(2, i))
        # Give a tolerance of 60 seconds to prevent test from becoming flaky
        # This large tolerance has been chosen intentionally
        assert abs(response_td - expected_td) <= timedelta(seconds=60)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        expire_email_lockout(data["username"])


def test_lockout_prevents_login(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    # Check if lockouts prevent even valid logins.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
    }

    lockout_email(client, data["username"])

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_successful_auth_resets_lockouts(
    db: None, user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    # Check if a successful login will reset the email's
    # lockouts and allow another five failed attempts.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    lockout_email(client, data["username"])
    expire_email_lockout(data["username"])
    data["password"] = "secret"

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_302_FOUND

    data["password"] = "wrongpasswordagain"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.content.find(b"Invalid login credentials") != -1


def test_password_reset_resets_lockouts(
    user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    # Check if a password reset will reset the email's
    # lockouts and allow another five failed attempts.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    lockout_email(client, data["username"])

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.content.find(b"This account is locked out for") != -1
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Reset and change password
    assert client.post(
        "/api/v3/users/forgotten_password",
        json.dumps({"email": user.email}),
        content_type="application/json",
        format="json"
    ).status_code == status.HTTP_200_OK
    code = ResetPasswordCode.get_code(user)
    assert code is not None

    session = client.session
    session.update({"reset_code": code.path})
    session.save()
    response = client.post(
        "/api/v3/users/reset_password",
        json.dumps({
            "new_password1": "samplenewpassword",
            "new_password2": "samplenewpassword",
        }),
        content_type="application/json",
        format="json"
    )
    assert response.status_code == status.HTTP_302_FOUND

    # See that the lockouts have been reset
    data["password"] = "wrongpasswordagain"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.content.find(b"Invalid login credentials") != -1

    # Try properly logging in
    data["password"] = "samplenewpassword"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_302_FOUND


def test_authentication_logging(
    user: WdaeUser, client: Client,
    tokens: tuple[AccessToken, AccessToken]
) -> None:
    # Check if both successful and unsuccessful
    # authentication attempts are logged.
    url = "/accounts/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert last_login is not None
    expected_time = timezone.now().replace(microsecond=0)
    login_time = last_login.time.replace(microsecond=0)
    assert response.status_code == status.HTTP_302_FOUND
    assert last_login.email == "user@example.com"
    # Give a tolerance of 5 seconds to prevent test from becoming flaky
    assert abs(login_time - expected_time) <= timedelta(seconds=5)
    assert last_login.failed_attempt == 0

    data["password"] = "wrongpassword"

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert last_login is not None

    expected_time = timezone.now().replace(microsecond=0)
    login_time = last_login.time.replace(microsecond=0)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert last_login.email == "user@example.com"
    # Give a tolerance of 5 seconds to prevent test from becoming flaky
    assert abs(login_time - expected_time) <= timedelta(seconds=5)
    assert last_login.failed_attempt == 1
