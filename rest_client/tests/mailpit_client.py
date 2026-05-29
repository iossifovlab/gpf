from __future__ import annotations

import logging
from typing import cast

import requests

logger = logging.getLogger(__name__)


class MailpitClient:
    """Mailpit REST client."""

    TIMEOUT = 30.0

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def get_all_messages(self) -> dict:
        """Get all messages from the Mailpit REST API."""
        url = f"{self.base_url}/api/v1/messages"
        response = self.session.get(url, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(f"Get all messages failed: {response.text}")
        return cast(dict, response.json())

    def delete_all_messages(self) -> None:
        """Delete all messages from the Mailpit REST API."""
        url = f"{self.base_url}/api/v1/messages"
        response = self.session.delete(url, json={}, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(f"Delete all messages failed: {response.text}")

    def find_message_to_user(self, useremail: str) -> dict:
        """Get a message to specific user from the Mailpit REST API."""
        search_url = f"{self.base_url}/api/v1/search"
        params = {"query": f"to:{useremail}"}
        response = self.session.get(
            search_url, params=params, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(
                f"Get message to {useremail} failed: {response.text}")
        messages = response.json()
        assert messages["count"] == 1
        message_id = messages["messages"][0]["ID"]

        message_url = f"{self.base_url}/api/v1/message/{message_id}"
        response = self.session.get(message_url, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(f"Get message {message_id} failed: {response.text}")
        return cast(dict, response.json())

    @staticmethod
    def get_email_text(message: dict) -> str:
        """Get message plain text body from the Mailpit REST API."""
        return cast(str, message["Text"])

    @staticmethod
    def get_email_to(message: dict) -> str:
        """Get message recipient address from the Mailpit REST API."""
        return cast(str, message["To"][0]["Address"])
