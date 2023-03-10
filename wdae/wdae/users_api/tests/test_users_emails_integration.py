# pylint: disable=W0621,C0114,C0116,W0212,W0613
import json
import requests
from rest_framework import status


def test_reset_pass_message_search(client, unique_test_user, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    url = "/api/v3/users/forgotten_password"
    data = {"email": unique_test_user.email}

    response = client.post(
        url, json.dumps(data), content_type="application/json", format="json"
    )
    assert response.status_code == status.HTTP_200_OK

    response = requests.get(
        f"http://{settings.EMAIL_HOST}:8025/api/v2/search",
        params={"kind": "to", "query": unique_test_user.email}, timeout=2.0)

    assert response.ok

    data = response.json()
    assert data["count"] == 1
    to_email = data["items"][0]["Content"]["Headers"]["To"]
    assert to_email == [unique_test_user.email]
