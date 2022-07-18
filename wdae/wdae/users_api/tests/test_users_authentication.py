import json
import pytest

from datetime import timedelta
from rest_framework import status
from django.utils import timezone

from users_api.views import LOCKOUT_THRESHOLD
from users_api.models import AuthenticationLog


def lockout_email(client, email):
    data = {
        "username": email,
        "password": "invalidpasswordinvalidpassword",
    }
    for i in range(0, LOCKOUT_THRESHOLD + 1):
        client.post(
            "/api/v3/users/login",
            json.dumps(data),
            content_type="application/json", format="json"
        )


def expire_email_lockout(email):
    """
    Wind back times of all logins so that the lockout expires.
    """
    query = AuthenticationLog.objects.filter(
        email__iexact=email
    ).order_by("-time", "-failed_attempt")
    last_login = AuthenticationLog.get_last_login_for(email)
    subtract_time = timedelta(
        seconds=pow(2, last_login.failed_attempt + 1 - LOCKOUT_THRESHOLD) * 60
    )
    for login in query:
        login.time = login.time - subtract_time
        login.save()


def test_successful_auth(db, user, client):
    url = "/api/v3/users/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_successful_auth_case_insensitive(db, user, client):
    url = "/api/v3/users/login"
    data = {
        "username": "UsER@ExAmPlE.cOm",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_failed_auth(db, user, client):
    url = "/api/v3/users/login"
    data = {"username": "bad@example.com", "password": "secret"}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_no_username_auth(db, user, client):
    url = "/api/v3/users/login"
    data = {"username": "", "password": "secret"}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_user_info_after_auth(user_client):
    response = user_client.get("/api/v3/users/get_user_info")
    assert response.data["loggedIn"] is True
    assert response.data["email"] == "user@example.com"


def test_email_auth_successful(db, user, client):
    """Try to login with an valid, existing email."""
    url = "/api/v3/users/login"
    data = {
        "username": "user@example.com",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_email_auth_unsuccessful(db, user, client):
    """Try to login with a non-existing email."""
    url = "/api/v3/users/login"
    data = {
        "username": "nonexistntuser@example.com",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_failed_auth_attempts(db, user, client):
    """Check if the user is allowed four failed
    login attempts before being locked out.
    """
    url = "/api/v3/users/login"
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
        assert last_login.failed_attempt == i + 1
        assert response.data is None
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert last_login.failed_attempt == LOCKOUT_THRESHOLD + 1
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_failed_auth_lockouts(db, user, client):
    """Check if progressive lockouts are working."""
    url = "/api/v3/users/login"
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
        assert "lockout_time" in response.data
        assert response.data["lockout_time"] == pytest.approx(
            pow(2, i) * 60, abs=5  # 5 second tolerance
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        expire_email_lockout(data["username"])


def test_lockout_prevents_login(db, user, client):
    """Check if lockouts prevent even valid logins."""
    url = "/api/v3/users/login"
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


def test_successful_auth_resets_lockouts(db, user, client):
    """Check if a successful login will reset the email's
    lockouts and allow another five failed attempts.
    """
    url = "/api/v3/users/login"
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
    assert response.status_code == status.HTTP_204_NO_CONTENT

    data["password"] = "wrongpasswordagain"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data is None


def test_password_reset_resets_lockouts(user, client):
    """Check if a password reset will reset the email's
    lockouts and allow another five failed attempts.
    """
    url = "/api/v3/users/login"
    data = {
        "username": "user@example.com",
        "password": "wrongpassword",
    }

    lockout_email(client, data["username"])

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert "lockout_time" in response.data
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Reset and change password
    assert client.post(
        "/api/v3/users/reset_password",
        json.dumps({"email": user.email}),
        content_type="application/json",
        format="json"
    ).status_code == status.HTTP_200_OK
    assert client.post(
        "/api/v3/users/change_password",
        json.dumps({
            "verifPath": user.verificationpath.path,
            "password": "samplenewpassword"
        }),
        content_type="application/json",
        format="json"
    ).status_code == status.HTTP_201_CREATED

    # See that the lockouts have been reset
    data["password"] = "wrongpasswordagain"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data is None

    # Try properly logging in
    data["password"] = "samplenewpassword"
    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_authentication_logging(user, client):
    """Check if both successful and unsuccessful authentication attempts
    are logged.
    """
    url = "/api/v3/users/login"
    data = {
        "username": "user@example.com",
        "password": "secret",
    }

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert last_login.email == "user@example.com"
    assert last_login.time == timezone.now().replace(microsecond=0)
    assert last_login.failed_attempt == 0

    data["password"] = "wrongpassword"

    response = client.post(
        url, json.dumps(data),
        content_type="application/json", format="json"
    )
    last_login = AuthenticationLog.get_last_login_for(data["username"])
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert last_login.email == "user@example.com"
    assert last_login.time == timezone.now().replace(microsecond=0)
    assert last_login.failed_attempt == 1
