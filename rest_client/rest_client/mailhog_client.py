from __future__ import annotations

import logging
from typing import cast

import requests

logger = logging.getLogger(__name__)


class MailhogClient:
    """Mailhog REST client."""

    TIMEOUT = 30.0

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def get_all_messages(self) -> dict:
        """Get all messages from the Mailhog REST API."""
        all_messages_url = f"{self.base_url}/api/v2/messages"
        response = self.session.get(
            all_messages_url, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(f"Get all messages failed: {response.text}")
        return cast(dict, response.json())

    def delete_all_messages(self) -> None:
        """Delete all messages from the Mailhog REST API."""
        all_messages_url = f"{self.base_url}/api/v1/messages"
        response = self.session.delete(
            all_messages_url, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(f"Delete all messages failed: {response.text}")

    def find_message_to_user(self, useremail: str) -> dict:
        """Get a message to specific user from the Mailhog REST API."""
        search_url = f"{self.base_url}/api/v2/search"
        params = {
            "kind": "to",
            "query": useremail,
        }
        response = requests.get(
            search_url, params=params, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise OSError(
                f"Get message to {useremail} failed: {response.text}")
        messages = response.json()
        assert messages["count"] == 1
        return cast(dict, messages["items"][0])

    @staticmethod
    def get_email_text(message: dict) -> str:
        """Get a message text from the Mailhog REST API."""
        return cast(str, message["Content"]["Body"])

    @staticmethod
    def get_email_to(message: dict) -> str:
        """Get a message to from the Mailhog REST API."""
        return cast(str, message["Content"]["Headers"]["To"][0])
