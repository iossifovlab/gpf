# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import Optional

from pprint import pprint

import pytest

from rest_framework import status  # type: ignore

from utils.email_regex import email_regex, is_email_valid
from utils.password_requirements import is_password_valid
from django.test.client import Client
from users_api.models import WdaeUser


def test_invalid_reset_code(client: Client, researcher: WdaeUser) -> None:
    url = "/api/v3/users/reset_password"
    session = client.session
    session.update({"reset_code": "asdasfasfgadg"})
    session.save()
    data = {
        "new_password1": "samplenewpassword",
        "new_password2": "samplenewpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_reset_pass(client: Client, researcher: WdaeUser) -> None:
    url = "/api/v3/users/forgotten_password"
    data = {"email": researcher.email}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK


def test_register_existing_user(client: Client, researcher: WdaeUser) -> None:
    url = "/api/v3/users/register"
    data = {
        "name": researcher.name,
        "email": researcher.email,
    }
    pprint(data)

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_email_regex_is_posix_compliant() -> None:
    assert r"+?" not in email_regex
    assert r"*?" not in email_regex
    assert r"(?:" not in email_regex
    assert r"\w" not in email_regex
    assert r"\d" not in email_regex


def test_email_validaiton() -> None:
    assert is_email_valid("test@test.com")
    assert is_email_valid("t3st@t3st.org")
    assert is_email_valid("test@test.uk")
    assert is_email_valid("te-st@test.com")
    assert is_email_valid("a@b.com")
    assert is_email_valid("UpperCase@email.com")

    assert not is_email_valid("abab")
    assert not is_email_valid("test@-test.com")
    assert not is_email_valid("test@com")
    assert not is_email_valid("@bla.com")
    assert not is_email_valid("invalid@UpperCaseDomain.com")
    assert not is_email_valid("invalid@uppercasedomain.Com")


def test_password_validation() -> None:
    generic_password = "esg09dusfd"

    # Don't accept passwords shorter than 10 symbols
    for i in range(0, 10):
        assert not is_password_valid(generic_password[:i])

    # Check if common password blacklist is used
    assert not is_password_valid("1234567890")
    assert not is_password_valid("qwertyuiop")
    assert not is_password_valid("qwerty123456")

    assert is_password_valid(generic_password)


@pytest.mark.parametrize(
    "page,status_code,length,first_email,last_email",
    [
        (
            1, status.HTTP_200_OK, 25,
            "admin@example.com", "user30@example.com"
        ),
        (
            2, status.HTTP_200_OK, 25,
            "user31@example.com", "user53@example.com"
        ),
        (
            3, status.HTTP_200_OK, 25,
            "user54@example.com", "user76@example.com"
        ),
        (
            4, status.HTTP_200_OK, 25,
            "user77@example.com", "user99@example.com"
        ),
        (5, status.HTTP_200_OK, 2, "user9@example.com", "user@example.com"),
        (6, status.HTTP_204_NO_CONTENT, None, None, None),
    ]
)
def test_users_pagination(
    admin_client: Client,
    hundred_users: list[WdaeUser],
    page: int, status_code: int,
    length: int,
    first_email: Optional[str],
    last_email: Optional[str]
) -> None:
    url = f"/api/v3/users?page={page}"
    response = admin_client.get(url)
    assert response.status_code == status_code

    if length is not None:
        assert len(response.json()) == length

    if first_email is not None:
        data = response.json()
        assert data[0]["email"] == first_email

    if last_email is not None:
        data = response.json()

        assert data[length - 1]["email"] == last_email


def test_users_search(
    admin_client: Client,
    hundred_users: list[WdaeUser]
) -> None:
    url = "/api/v3/users?search=user9"
    response = admin_client.get(url)
    assert len(response.json()) == 11


@pytest.mark.parametrize(
    "page,status_code,length",
    [
        (1, status.HTTP_200_OK, 25),
        (2, status.HTTP_200_OK, 25),
        (3, status.HTTP_200_OK, 25),
        (4, status.HTTP_200_OK, 25),
        (5, status.HTTP_200_OK, 1),
        (6, status.HTTP_204_NO_CONTENT, None),
    ]
)
def test_users_search_pagination(
    admin_client: Client,
    hundred_users: list[WdaeUser],
    page: int,
    status_code: int,
    length: Optional[int]
) -> None:
    url = f"/api/v3/users?page={page}&search=user"
    response = admin_client.get(url)
    assert response.status_code == status_code
    if length is not None:
        data = response.json()
        assert len(data) == length
        for idx, user in enumerate(data):
            print(f"{idx}: {user['email']}")
