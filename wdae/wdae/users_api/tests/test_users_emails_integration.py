# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json

import requests
from django.test.client import Client
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status

from users_api.models import WdaeUser


def test_reset_pass_message_search(
    client: Client, unique_test_user: WdaeUser, settings: SettingsWrapper,
) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    url = "/api/v3/users/forgotten_password"
    data = {"email": unique_test_user.email}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    mail_check = requests.get(
        f"http://{settings.EMAIL_HOST}:8025/api/v2/search",
        params={"kind": "to", "query": unique_test_user.email}, timeout=2.0)

    assert mail_check.ok

    data = mail_check.json()
    assert data["count"] == 1
    to_email = data["items"][0]["Content"]["Headers"]["To"]
    assert to_email == [unique_test_user.email]
