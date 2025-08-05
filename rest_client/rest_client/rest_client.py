import logging
import urllib.parse
from collections.abc import Generator, Iterable, Iterator
from typing import Any, Protocol, cast

import ijson
import requests
from dae.pheno.common import MeasureType
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


class GPFAnonymousSession(GPFClientSession):
    """GPF anonymous REST client."""

    DEFAULT_TIMEOUT = 10

    def __init__(
        self, base_url: str,
    ):
        self._base_url = base_url

    def base_url(self) -> str:
        return self._base_url

    def authenticate(self) -> None:
        pass

    def deauthenticate(self) -> None:
        pass

    def get(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Get request."""
        headers = headers or {}
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
        headers = headers or {}
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        return requests.put(
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )


class GPFOAuthSession(GPFClientSession):
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
        request_headers = headers or {}
        request_headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        def make_request() -> requests.Response:
            headers = request_headers

            return requests.get(
                url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        response = make_request()
        if response.status_code == 401:
            self.refresh_token()
            request_headers["Authorization"] = f"Bearer {self.token}"
            response = make_request()
        return response

    def post(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Post request."""
        request_headers = headers or {}
        request_headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        def make_request() -> requests.Response:
            headers = request_headers

            return requests.post(
                url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        response = make_request()
        if response.status_code == 401:
            self.refresh_token()
            request_headers["Authorization"] = f"Bearer {self.token}"
            response = make_request()
        return response

    def put(
        self, url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Put request."""
        if self.token is None:
            self.authenticate()
        request_headers = headers or {}
        request_headers["Authorization"] = f"Bearer {self.token}"
        timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)

        def make_request() -> requests.Response:
            headers = request_headers

            return requests.put(
                url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        response = make_request()
        if response.status_code == 401:
            self.refresh_token()
            request_headers["Authorization"] = f"Bearer {self.token}"
            response = make_request()
        return response


class GPFPasswordSession(GPFClientSession):
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

    def __init__(
        self, session: GPFClientSession, client_id: str = "rest",
    ) -> None:
        self.session = session
        self._client_id = client_id

    @property
    def base_url(self) -> str:
        return self.session.base_url()

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/v3"

    @property
    def client_id(self) -> str:
        return self._client_id

    @staticmethod
    def build_query_string(query_values: dict[str, Any]) -> str:
        """Build a query string from a dictionary of query values."""
        query_values_str = ""
        first = True
        for key, val in query_values.items():
            if val is None:
                continue
            query_values_str += "?" if first else "&"
            query_values_str += f"{key}={val}"
            first = False
        return query_values_str

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
            json=data,
            headers={"Content-Type": "application/json"},
        )
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

    def get_visible_datasets(self) -> list:
        datasets_url = f"{self.base_url}/api/v3/datasets/visible"
        response = self.session.get(datasets_url)
        data = response.json()
        return cast(list, data)

    def get_federation_datasets(self) -> list[dict]:
        datasets_url = f"{self.base_url}/api/v3/datasets/federation"
        response = self.session.get(datasets_url)
        data = response.json()
        return cast(list, data)

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
        timeout: float = 10.0,
    ) -> Iterator[Any]:
        """Perform a genotype browser query to the GPF API."""
        url = f"{self.base_url}/api/v3/genotype_browser/query"
        response = self.session.post(
            url,
            json=query,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=timeout,
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

    def get_families(
        self, dataset_id: str,
        timeout: float = 200.0,
    ) -> list[dict]:
        """Get families for a dataset."""
        url = f"{self.base_url}/api/v3/families/{dataset_id}/all"
        response = self.session.get(url, timeout=timeout)
        if response.status_code != 200:
            raise RESTError(f"Get families failed: {response.text}")
        return cast(list[dict], response.json())

    def get_denovo_gene_sets_db(
        self, timeout: float = 200.0,
    ) -> dict:
        """Get denovo gene sets db."""
        url = f"{self.base_url}/api/v3/gene_sets/denovo_gene_sets_db"
        response = self.session.get(url, timeout=timeout)
        if response.status_code != 200:
            raise RESTError(f"Get denovo gene sets db failed: {response.text}")
        return cast(dict, response.json())

    @staticmethod
    def _read_json_list_stream(
        response: requests.Response,
        *,
        _multiple_values: bool = False,
    ) -> Generator[Any, None, None]:
        assert response.status_code == 200
        stream = response.iter_content()
        objects = ijson.sendable_list()
        coro = ijson.items_coro(
            objects, "item", use_float=True, multiple_values=False,
        )
        for chunk in stream:
            coro.send(chunk)
            if len(objects) > 0:
                yield from objects
                del objects[:]

    def get_datasets(self) -> list[dict]:
        return self.get_federation_datasets()

    def get_variants_preview(self, data: dict) -> requests.Response:
        return self.session.post(
            f"{self.api_url}/genotype_browser/preview/variants",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
        )

    def post_query_variants(
        self, data: dict, *, reduce_alleles: bool = False,
    ) -> Generator[Any, None, None]:
        """Post query request for variants preview."""
        assert data.get("download", False) is False
        data["reduceAlleles"] = reduce_alleles
        response = self.session.post(
            f"{self.api_url}/genotype_browser/query",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        return self._read_json_list_stream(response)

    def post_query_variants_download(
        self, data: dict,
    ) -> Generator[Any, None, None]:
        """Post query request for variants download."""
        data["download"] = True
        response = self.session.post(
            f"{self.api_url}/genotype_browser/query",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        return self._read_json_list_stream(response)

    def post_gene_view_summary_variants(
        self, data: dict,
    ) -> Generator[Any, None, None]:
        """Post query request for gene view summary variants."""
        response = self.session.post(
            f"{self.api_url}/gene_view/query_summary_variants",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        return self._read_json_list_stream(response)

    def post_gene_view_summary_variants_download(
        self, data: dict,
    ) -> requests.Response:
        """Post query request for gene view summary variants download."""
        return self.session.post(
            f"{self.api_url}/gene_view/download_summary_variants",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True,
        )

    def get_member_details(
        self, dataset_id: str, family_id: str, member_id: str,
    ) -> Any:
        """Get family member details."""
        response = self.session.get(
            f"{self.api_url}/families/"
            f"{dataset_id}/{family_id}/members/{member_id}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_member_details(
        self, dataset_id: str, family_id: str,
    ) -> Any:
        """Get all family members details."""
        response = self.session.get(
            f"{self.api_url}/families/{dataset_id}/{family_id}/members/all",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_members(self, dataset_id: str, family_id: str) -> Any:
        """Get family members."""
        response = self.session.get(
            f"{self.api_url}/families/{dataset_id}/{family_id}/members",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_family_details(
        self, dataset_id: str, family_id: str,
    ) -> Any:
        """Get a family details."""
        response = self.session.get(
            f"{self.api_url}/families/{dataset_id}/{family_id}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_family_details(self, dataset_id: str) -> list[dict]:
        return self.get_families(dataset_id)

    def get_person_set_collection_configs(self, dataset_id: str) -> Any:
        """Get person set collection configuration for a dataset."""
        response = self.session.get(
            f"{self.api_url}/person_sets/{dataset_id}/configs")

        if response.status_code != 200:
            return None

        return response.json()

    def get_common_report(
        self, common_report_id: str, *, full: bool = False,
    ) -> Any:
        """Get the commont report for a dataset."""
        if full:
            url = (
                f"{self.api_url}/common_reports"
                f"/studies/{common_report_id}/full"
            )
        else:
            url = f"{self.api_url}/common_reports/studies/{common_report_id}"
        response = self.session.get(url)
        return response.json()

    def get_common_report_families_data(
        self, common_report_id: str,
    ) -> Any:
        """Get families part of the common report for a study."""
        return self.session.post(
            f"{self.api_url}/common_reports/families_data/{common_report_id}",
            stream=True,
        )

    def get_pheno_browser_config(self, db_name: str) -> Any:
        """Get the pheno browser congigruation."""
        query_str = self.build_query_string({
            "db_name": db_name,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/config{query_str}",
        )
        return response.json()

    def get_browser_measures_info(self, dataset_id: str) -> Any:
        """Get pheno browser measuers info for a dataset."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser"
            f"/measures_info{query_str}",
        )
        return response.json()

    def get_browser_measures(
        self,
        dataset_id: str, *,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> Any:
        """Get pheno measures that correspond to a search."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
            "instrument": instrument,
            "search": search_term,
            "page": page,
            "sort_by": sort_by,
            "order_by": order_by,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/measures{query_str}",
            stream=True,
        )
        return self._read_json_list_stream(response)

    def get_measures_list(
        self,
        dataset_id: str,
    ) -> Any:
        """Get pheno measures in a list format."""
        query_str = self.build_query_string({
            "datasetId": dataset_id,
        })
        response = self.session.get(
            f"{self.api_url}/measures/list{query_str}",
            stream=True,
        )
        return response.json()

    def get_instruments(self, dataset_id: str) -> Any:
        """Get instruments for a pheno measure."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/instruments{query_str}",
        )
        return response.json()["instruments"]

    def get_browser_measure_count(
        self,
        dataset_id: str,
        instrument: str | None,
        search_term: str | None,
    ) -> int:
        """Post download request for pheno measures."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
            "search_term": search_term,
            "instrument": instrument,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/measures_count{query_str}",
            stream=True,
        )
        if response.status_code != 200:
            raise ValueError(
                f"{self.client_id}: Failed to get measure count"
                f"from {dataset_id}",
            )
        res = response.json()
        if "count" not in res:
            raise ValueError(f"{self.client_id}: Invalid response")

        return cast(int, res["count"])

    def get_measures_download(
            self, dataset_id: str,
            search_term: str | None = None,
            instrument: str | None = None,
    ) -> Any:
        """Post download request for pheno measures."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
            "search_term": search_term,
            "instrument": instrument,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/download{query_str}",
            stream=True,
        )
        return response.iter_content()

    def get_enrichment_models(self, dataset_id: str) -> dict[str, Any]:
        """Return enrichment models available for the study."""
        response = self.session.get(
            f"{self.api_url}/enrichment/models/{dataset_id}")
        if response.status_code != 200:
            return {}
        return cast(dict[str, Any], response.json())

    def post_enrichment_test(self, query: dict) -> Any:
        """Return enrichment test result."""
        response = self.session.post(
            f"{self.api_url}/enrichment/test",
            json=query,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            raise RESTError(response.status_code)
        return response.json()

    def get_instruments_details(self, dataset_id: str) -> Any:
        """Get instruments details for a dataset."""
        query_str = self.build_query_string({
            "datasetId": dataset_id,
        })

        return self.session.get(
            f"{self.api_url}/pheno_tool/instruments{query_str}",
        ).json()

    def get_measure(self, dataset_id: str, measure_id: str) -> Any:
        """Get a measure in a dataset."""
        query_str = self.build_query_string({
            "datasetId": dataset_id,
            "measureId": measure_id,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_tool/measure{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measure_description(self, dataset_id: str, measure_id: str) -> Any:
        """Get a measure description."""
        query_str = self.build_query_string({
            "dataset_id": dataset_id,
            "measure_id": measure_id,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/measure_description{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_pheno_browser_measures(
        self, dataset_id: str,
        instrument_name: str | None,
        search_term: MeasureType | None,
    ) -> Any:
        """Get measures for a dataset."""

        query_str = self.build_query_string({
            "dataset_id": dataset_id,
            "instrument": instrument_name,
            "search": search_term,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_browser/measures{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measures(
        self, dataset_id: str,
        instrument_name: str | None,
        measure_type: MeasureType | None,
    ) -> Any:
        """Get measures for a dataset."""
        measure_t = measure_type.name if measure_type is not None else None

        query_str = self.build_query_string({
            "datasetId": dataset_id,
            "instrument": instrument_name,
            "measureType": measure_t,
        })
        response = self.session.get(
            f"{self.api_url}/pheno_tool/measures{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_regressions(self, dataset_id: str) -> Any:
        """Get pheno measures regressions in a dataset."""
        query_str = self.build_query_string({
            "datasetId": dataset_id,
        })
        response = self.session.get(
            f"{self.api_url}/measures/regressions{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def post_measures_values(
        self, dataset_id: str,
        measure_ids: Iterable[str],
        person_ids: Iterable[str] | None = None,
        family_ids: Iterable[str] | None = None,
        roles: Iterable[str] | None = None,
    ) -> Any:
        """Post pheno measure values request."""
        data = {
            "datasetId": dataset_id,
            "measureIds": measure_ids,
            "personIds": person_ids,
            "familyIds": family_ids,
            "roles": roles,
        }
        response = self.session.post(
            f"{self.api_url}/pheno_tool/people_values",
            json=data,
            headers={"Content-Type": "application/json"},
        )

        return response.json()

    def post_measure_values(
        self, dataset_id: str,
        measure_id: str,
        person_ids: Iterable[str] | None,
        family_ids: Iterable[str] | None,
        roles: Iterable[str] | None,
    ) -> Any:
        """Post pheno measure values request."""
        return self.post_measures_values(
            dataset_id, [measure_id], person_ids, family_ids, roles,
        )

    def post_pheno_tool(self, data: dict) -> Any:
        """Post pheno tool request."""
        response = self.session.post(
            f"{self.api_url}/pheno_tool",
            json=data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_gene_set_collections(self) -> Any:
        """Get gene set collections."""
        response = self.session.get(
            f"{self.api_url}/gene_sets/gene_sets_collections",
        )

        if response.status_code != 200:
            logger.warning(
                "error while looking for gene sets collections; %s: (%s)",
                response.status_code, response)
            return []

        return response.json()

    def get_gene_sets(
        self, collection_id: str,
    ) -> list[dict[str, Any]] | None:
        """Get a gene set from a gene set collection."""
        response = self.session.post(
            f"{self.api_url}/gene_sets/gene_sets",
            json={"geneSetsCollection": collection_id},
        )

        if response.status_code != 200:
            return None

        return cast(list[dict[str, Any]], response.json())

    def get_gene_set_download(
        self, gene_sets_collection: str, gene_set: str,
    ) -> Any:
        """Download a gene set."""
        query_str = self.build_query_string({
            "geneSetsCollection": gene_sets_collection,
            "geneSet": gene_set,
        })
        response = self.session.get(
            f"{self.api_url}/gene_sets/gene_set_download{query_str}",
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def has_denovo_gene_sets(self) -> bool:
        response = self.session.get(f"{self.api_url}/gene_sets/has_denovo")
        return response.status_code == 204

    def get_denovo_gene_sets(self, gene_set_types: dict) -> Any:
        """Get denovo gene sets."""
        logger.debug(
            "getting denovo gene sets for: %s", gene_set_types)

        response = self.session.post(
            f"{self.api_url}/gene_sets/gene_sets",
            json={
                "geneSetsCollection": "denovo",
                "geneSetsTypes": gene_set_types,
            },
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_denovo_gene_set(
        self, gene_set_id: str, gene_set_types: dict,
    ) -> Any:
        """Get a denovo gene set."""
        response = self.session.post(
            f"{self.api_url}/gene_sets/gene_set_download",
            json={
                "geneSetsCollection": "denovo",
                "geneSet": gene_set_id,
                "geneSetsTypes": gene_set_types,
            },
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def get_genomic_scores(self) -> list[dict[str, Any]] | None:
        response = self.session.get(
            f"{self.api_url}/genomic_scores/score_descs")
        if response.status_code != 200:
            return None
        return cast(list[dict[str, Any]], response.json())

    def get_genomic_score(self, score_id: str) -> dict[str, Any] | None:
        response = self.session.get(
            f"{self.api_url}/genomic_scores/score_descs/{score_id}")
        if response.status_code != 200:
            return None
        return cast(dict[str, Any], response.json()[0])

    def get_pheno_image(
        self, image_path: str,
    ) -> tuple[bytes | None, str | None]:
        """
        Return tuple of image bytes and image type from remote.

        Accesses static files on the remote GPF instance.
        """
        url = f"{self.api_url}/static/{image_path}"
        response = requests.get(url, timeout=300_000)
        if response.status_code != 200:
            return None, None

        return response.content, response.headers["content-type"]
