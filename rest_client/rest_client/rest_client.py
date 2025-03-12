import logging
import urllib.parse
from collections.abc import Iterator
from typing import Any, Protocol, cast

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class RESTError(BaseException):
    """REST error."""


def encode_params_utf8(
    params: list[tuple[str, str]],
) -> list[tuple[bytes, bytes]]:
    """Ensures that all parameters in a list of 2-element tuples are encoded to
    bytestrings using UTF-8
    """
    encoded = []
    for k, v in params:
        encoded.append((
            k.encode("utf-8") if isinstance(k, str) else k,
            v.encode("utf-8") if isinstance(v, str) else v))
    return encoded


def urlencode(params: list[tuple[str, str]]) -> str:
    utf8_params = encode_params_utf8(params)
    urlencoded = urllib.parse.urlencode(utf8_params)
    if isinstance(urlencoded, str):
        return urlencoded
    return urlencoded.decode("utf-8")


class GPFClientSession(Protocol):
    """GPF Client Session protocl."""

    def base_url(self) -> str:
        ...

    def authenticate(self) -> None:
        ...

    def deauthenticate(self) -> None:
        ...

    def get(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        ...

    def post(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        ...

    def put(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        ...


class GPFConfidentialClient:
    """GPF Rest Client."""

    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        self._base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = f"{base_url}/o/token/"
        self.redirect_uri = redirect_uri
        self.token: str | None = None

    def base_url(self) -> str:
        return self._base_url

    def authenticate(self) -> None:
        """Authenticate, second try."""
        params = [
            ("grant_type", "client_credentials"),
        ]
        body = urlencode(params)
        auth = HTTPBasicAuth(self.client_id, self.client_secret)

        with requests.post(
            self.token_url,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=body,
            auth=auth,
            timeout=self.DEFAULT_TIMEOUT,
        ) as response:
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to obtain token for <{self.client_id}> "
                    f"from <{self._base_url}>",
                )
        self.token = response.json()["access_token"]

    def refresh_token(self) -> None:
        self.authenticate()

    def revoke_token(self) -> None:
        """Revoke OAuth2 token."""
        if self.token is None:
            raise ValueError("No token to revoke")
        token_url = f"{self._base_url}/o/revoke_token/"
        params = [
            ("token", self.token),
        ]
        body = urlencode(params)
        auth = HTTPBasicAuth(self.client_id, self.client_secret)

        with requests.post(
                    token_url,
                    headers={
                        "Cache-Control": "no-cache",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data=body,
                    auth=auth,
                    timeout=self.DEFAULT_TIMEOUT,
                ) as response:
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to revoke token from {self._base_url}",
                )
        self.token = None

    def deauthenticate(self) -> None:
        """Deauthenticate."""
        self.revoke_token()

    def get(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Get request."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return requests.get(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def post(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Post request."""
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return requests.post(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def put(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Put request."""
        if self.token is None:
            self.authenticate()
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return requests.put(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )


class GPFBasicAuth:
    """Basic auth session"""

    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        """Setup and login to the GPF REST API."""
        self.session = requests.Session()
        self._base_url = base_url
        self.username = username
        self.password = password

    def base_url(self) -> str:
        return self._base_url

    def authenticate(self) -> None:
        """Login to the GPF REST API."""
        body = {
            "username": self.username,
            "password": self.password,
        }

        login_url = f"{self._base_url}/api/v3/users/login"

        response = self.session.post(
            login_url, json=body,
            timeout=self.DEFAULT_TIMEOUT)
        if response.status_code != 204:
            raise RESTError(f"Login failed: {response.text}")
        logger.debug("Login successful: %s", response.text)

    def deauthenticate(self) -> None:
        logout_url = f"{self._base_url}/api/v3/users/logout"
        response = self.session.post(
            logout_url, timeout=self.DEFAULT_TIMEOUT)
        if response.status_code != 204:
            raise RESTError(f"Logout failed: {response.text}")
        logger.debug("Logout successful: %s", response.text)

    def get(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Get request."""
        headers = headers or {}
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return self.session.get(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def post(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Post request."""
        headers = headers or {}
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return self.session.post(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    def put(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Put request."""
        headers = headers or {}
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return self.session.put(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )


class RESTClient:
    """REST client for the GPF users and groups REST API."""

    def __init__(self, session: GPFClientSession) -> None:
        self.session = session

    @property
    def base_url(self) -> str:
        return self.session.base_url()

    def login(self) -> None:
        """Login to the GPF REST API."""
        self.session.authenticate()

    def logout(self) -> None:
        """Logout from the GPF REST API."""
        self.session.deauthenticate()

    def get_all_users(self) -> list[dict]:
        """Get all users from the GPF users REST API."""
        all_users_url = f"{self.base_url}/api/v3/users"
        response = self.session.get(all_users_url)
        if response.status_code != 200:
            data = response.json()
            raise RESTError(f"Get all users failed: {data['detail']}")
        return cast(list[dict], response.json())

    def get_user(self, user_id: int) -> dict:
        """Get a user from the GPF users REST API."""
        response = self.session.get(
            f"{self.base_url}/api/v3/users/{user_id}")
        if response.status_code != 200:
            data = response.json()
            raise RESTError(f"Get user failed: {data['detail']}")
        return cast(dict, response.json())

    def create_user(
        self, username: str, name: str,
        groups: list[str] | None = None,
    ) -> dict:
        """Create a user in the GPF users REST API."""
        body = {
            "email": username,
            "name": name,
            "groups": [
                "any_user",
                username,
                *(groups or []),
            ],
        }
        users_url = f"{self.base_url}/api/v3/users"
        response = self.session.post(
            users_url, json=body)
        if response.status_code != 201:
            data = response.json()
            if "detail" in data:
                msg = data["detail"]
            elif "email" in data:
                msg = ";".join(data["email"])
            else:
                msg = response.text
            raise RESTError(f"Create user <{username}> failed: {msg}")
        return cast(dict, response.json())

    def update_user(self, user_id: int, data: dict) -> dict:
        """Update a user in the GPF users REST API."""
        response = self.session.put(
            f"{self.base_url}/api/v3/users/{user_id}",
            json=data)
        if response.status_code != 200:
            data = response.json()
            raise RESTError(f"Update user failed: {data['detail']}")
        return cast(dict, response.json())

    def get_all_datasets(self) -> list[dict]:
        datasets_url = f"{self.base_url}/api/v3/datasets"
        response = self.session.get(datasets_url)
        data = response.json()
        return cast(list[dict], data["data"])

    def get_dataset(self, dataset_id: str) -> dict:
        datasets_url = f"{self.base_url}/api/v3/datasets/{dataset_id}"
        response = self.session.get(datasets_url)
        data = response.json()
        return cast(dict, data["data"])

    def get_all_groups(self) -> list[dict]:
        """Get all groups from the GPF groups REST API."""
        groups_url = f"{self.base_url}/api/v3/groups"
        response = self.session.get(groups_url)
        if response.status_code != 200:
            data = response.json()
            msg = data.get("detail", response.text)
            raise RESTError(f"Get all groups failed: {msg}")
        return cast(list[dict], response.json())

    def get_group(self, group_name: str) -> dict:
        """Get a group from the GPF groups REST API."""
        groups_url = f"{self.base_url}/api/v3/groups/{group_name}"
        response = self.session.get(groups_url)
        if response.status_code != 200:
            data = response.json()
            msg = data.get("detail", response.text)
            raise RESTError(f"Get group {group_name} failed: {msg}")

        return cast(dict, response.json())

    def grant_permission(self, dataset_id: int, group_name: str) -> None:
        """Grant permission to a dataset."""
        body = {
            "datasetId": dataset_id,
            "groupName": group_name,
        }

        response = self.session.post(
            f"{self.base_url}/api/v3/groups/grant-permission", json=body)

        if response.status_code != 200:
            raise RESTError(f"Grant permission failed: {response.text}")

    def revoke_permission(self, dataset_id: int, group_id: int) -> None:
        """Revoke permission to a dataset."""
        body = {
            "datasetId": dataset_id,
            "groupId": group_id,
        }

        response = self.session.post(
            f"{self.base_url}/api/v3/groups/revoke-permission", json=body)

        if response.status_code != 200:
            raise RESTError(f"Revoke permission failed: {response.text}")

    def search_users(self, search: str) -> list[dict]:
        """Search for users in the GPF users REST API."""
        response = self.session.get(
            f"{self.base_url}/api/v3/users?page=1&search={search}")
        if response.status_code != 200:
            raise RESTError(f"Search user failed: {response.text}")
        return cast(list[dict], response.json())

    def initiate_forgotten_password(self, username: str) -> None:
        """Initiate forgotten password reset."""
        body = {
            "email": username,
        }
        response = self.session.post(
            f"{self.base_url}/api/v3/users/forgotten_password", json=body)
        if response.status_code != 200:
            raise RESTError(
                f"Initiate forgotten password reset failed: {response.text}")

    def initiate_password_reset_old(self, user_id: int) -> None:
        """Initiate password reset."""
        reset_password_url = \
            f"{self.base_url}/api/v3/users/{user_id}/password_reset"

        response = self.session.post(
            reset_password_url,
            json={})
        if response.status_code != 204:
            raise RESTError(
                f"Initiate old password reset failed: {response.text}")

    def query_genotype_browser(
        self, query: dict,
        chunk_size: int = 512,
    ) -> Iterator[Any]:
        """Perform a genotype browser query to the GPF API."""
        url = f"{self.base_url}/api/v3/genotype_browser/query"
        response = self.session.post(
            url,
            json=query,
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        if response.status_code != 200:
            raise RESTError(
                f"Query failed: {response.status_code} {response.text}")
        return response.iter_content(chunk_size=chunk_size)

    def query_pheno_tool(
        self, query: dict,
        chunk_size: int = 512,
    ) -> Iterator[Any]:
        """Perform a pheno tool query to the GPF API."""
        url = f"{self.base_url}/api/v3/pheno_tool"
        response = self.session.post(
            url,
            json=query,
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        if response.status_code != 200:
            raise OSError(f"Query failed: {response.text}")
        return response.iter_content(chunk_size=chunk_size)

    def query_summary_variants(
        self, query: dict,
    ) -> list:
        """Perform a summary variants query to the GPF API."""
        url = f"{self.base_url}/api/v3/gene_view/query_summary_variants"
        with self.session.post(
                    url,
                    json=query,
                    headers={"Content-Type": "application/json"},
                ) as response:

            if response.status_code != 200:
                raise RESTError(
                    f"Query failed: {response.status_code} {response.text}")
            return cast(list[dict], response.json())
