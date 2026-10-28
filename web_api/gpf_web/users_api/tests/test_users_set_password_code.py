# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import pytest
from django.test.client import Client
from rest_framework import status
from utils.password_requirements import is_password_valid

from users_api.models import ResetPasswordCode, SetPasswordCode, WdaeUser

SET_URL = "/api/v3/users/set_password"
RESET_URL = "/api/v3/users/reset_password"
NEW_PASSWORD = "samplenewpassword"  # ruff: ignore[hardcoded-password-string]


def post_new_password(client: Client, url: str) -> int:
    response = client.post(
        url,
        json.dumps({
            "new_password1": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        }),
        content_type="application/json",
    )
    return response.status_code


@pytest.mark.django_db
@pytest.mark.usefixtures("oauth_app")
def test_completed_reset_deletes_both_codes_of_the_user(
    researcher_without_password: WdaeUser,
) -> None:
    user = researcher_without_password
    SetPasswordCode.create(user)
    reset_code = ResetPasswordCode.create(user)
    client = Client()

    response = client.get(RESET_URL, {"code": reset_code.path})
    assert response.status_code == status.HTTP_200_OK
    assert post_new_password(client, RESET_URL) == status.HTTP_302_FOUND

    assert not SetPasswordCode.objects.filter(user=user).exists()
    assert not ResetPasswordCode.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_set_password_get_refuses_the_code_of_an_active_user(
    researcher: WdaeUser,
) -> None:
    code = SetPasswordCode.objects.create(user=researcher, path="set-code")

    response = Client().get(SET_URL, {"code": code.path})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not SetPasswordCode.objects.filter(pk=code.pk).exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("oauth_app")
def test_set_password_post_refuses_the_code_of_a_user_activated_after_get(
    researcher_without_password: WdaeUser,
) -> None:
    user = researcher_without_password
    code = SetPasswordCode.create(user)
    client = Client()
    response = client.get(SET_URL, {"code": code.path})
    assert response.status_code == status.HTTP_200_OK
    user.set_password("old-password-1")
    user.save()
    assert is_password_valid(NEW_PASSWORD)

    status_code = post_new_password(client, SET_URL)

    assert status_code == status.HTTP_400_BAD_REQUEST
    assert not SetPasswordCode.objects.filter(pk=code.pk).exists()
    user.refresh_from_db()
    assert user.check_password("old-password-1")
