# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
from typing import TYPE_CHECKING

import pytest
from django.test.client import Client
from rest_framework import status

from users_api.forms import WdaeResetPasswordForm
from users_api.models import ResetPasswordCode, SetPasswordCode, WdaeUser

if TYPE_CHECKING:
    # The django-stubs type of a test client response. It exists only in
    # the stubs, so it is imported only for the type checker.
    from django.test.client import _MonkeyPatchedWSGIResponse

DEFAULT_REDIRECT_URI = "http://localhost:4200/datasets"


def post_new_password(
    client: Client, url: str, session_key: str, code_path: object,
    password: str,
) -> "_MonkeyPatchedWSGIResponse":
    session = client.session
    session.update({session_key: str(code_path)})
    session.save()
    return client.post(
        url,
        json.dumps({
            "new_password1": password,
            "new_password2": password,
        }),
        content_type="application/json",
        format="json",
    )


def assert_password_invalid_error(
    response: "_MonkeyPatchedWSGIResponse",
) -> None:
    form = response.context["form"]
    assert form.has_error("new_password1", code="password_invalid")
    assert form.errors["new_password1"] == [
        str(WdaeResetPasswordForm.error_messages["password_invalid"]),
    ]


@pytest.mark.usefixtures("tokens")
def test_reset_password_refuses_short_password(
    client: Client, researcher: WdaeUser,
) -> None:
    code = ResetPasswordCode.create(researcher)

    response = post_new_password(
        client, "/api/v3/users/reset_password", "reset_code", code.path,
        "ninechars",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert_password_invalid_error(response)
    researcher.refresh_from_db()
    assert researcher.check_password("alabala")
    assert ResetPasswordCode.objects.filter(path=code.path).exists()


@pytest.mark.usefixtures("tokens")
def test_set_password_refuses_blacklisted_password(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    code = SetPasswordCode.create(researcher_without_password)

    response = post_new_password(
        client, "/api/v3/users/set_password", "set_code", code.path,
        "qwertyuiop",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert_password_invalid_error(response)
    researcher_without_password.refresh_from_db()
    assert not researcher_without_password.is_active
    assert SetPasswordCode.objects.filter(path=code.path).exists()


@pytest.mark.usefixtures("tokens")
def test_reset_password_accepts_valid_password(
    client: Client, researcher: WdaeUser,
) -> None:
    code = ResetPasswordCode.create(researcher)

    response = post_new_password(
        client, "/api/v3/users/reset_password", "reset_code", code.path,
        "tenletters",
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == DEFAULT_REDIRECT_URI
    researcher.refresh_from_db()
    assert researcher.check_password("tenletters")


@pytest.mark.usefixtures("tokens")
def test_set_password_accepts_valid_password(
    client: Client, researcher_without_password: WdaeUser,
) -> None:
    code = SetPasswordCode.create(researcher_without_password)

    response = post_new_password(
        client, "/api/v3/users/set_password", "set_code", code.path,
        "tenletters",
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"] == DEFAULT_REDIRECT_URI
    researcher_without_password.refresh_from_db()
    assert researcher_without_password.is_active
    assert researcher_without_password.check_password("tenletters")
