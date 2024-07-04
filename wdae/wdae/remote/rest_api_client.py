import logging
from collections.abc import Generator, Iterable
from typing import Any, Dict, List, Tuple, cast

import ijson
import requests

logger = logging.getLogger(__name__)


class RESTClientRequestError(Exception):

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message


class RESTClient:
    # pylint: disable=too-many-public-methods
    """Class defining WDAE REST API client."""

    DEFAULT_TIMEOUT = 300_000

    def __init__(
            self, remote_id: str, host: str, credentials: str,
            base_url: str | None = None,
            port: int | None = None,
            protocol: str | None = None,
            gpf_prefix: str | None = None):
        self.host = host
        self.remote_id = remote_id
        self.credentials = credentials
        self.token = None
        if base_url:
            if not base_url.endswith("/"):
                base_url = f"{base_url}/"
            if not base_url.startswith("/"):
                base_url = f"/{base_url}"
            self.base_url = base_url
        else:
            self.base_url = "/"

        self.port = port or None
        self.protocol = protocol or "http"
        self.gpf_prefix = gpf_prefix or None

        self._refresh_token()

    def _refresh_token(self) -> None:
        prefix = f"/{self.gpf_prefix}" if self.gpf_prefix else ""
        token_url = f"{self.build_host_url()}{prefix}/o/token/"
        response = requests.post(
            token_url,
            headers={"Authorization": f"Basic {self.credentials}",
                     "Cache-Control": "no-cache",
                     "Content-Type": "application/json"},
            json={"grant_type": "client_credentials"},
            timeout=self.DEFAULT_TIMEOUT,
        )
        if response.status_code != 200:
            raise RESTClientRequestError(
                f"Failed to obtain token from {self.remote_id}",
            )
        self.token = response.json()["access_token"]

    def build_host_url(self) -> str:
        if self.port:
            return f"{self.protocol}://{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}"

    def build_api_base_url(self) -> str:
        host_url = self.build_host_url()
        if self.gpf_prefix:
            return f"{host_url}/{self.gpf_prefix}{self.base_url}"
        return f"{host_url}{self.base_url}"

    def build_image_url(self, url: str) -> str:
        """Build a url for accessing remote GPF static images."""
        host_url = self.build_host_url()
        if self.gpf_prefix:
            return f"{host_url}/{self.gpf_prefix}/static/images/{url}"
        return f"{host_url}/static/images/{url}"

    def _build_url(
        self, url: str, query_values: dict | None = None,
    ) -> str:
        query_url = url
        if query_values:
            first = True
            for key, val in query_values.items():
                if val is None:
                    continue
                query_url += "?" if first else "&"
                query_url += f"{key}={val}"
                first = False
        base = self.build_api_base_url()
        result = f"{base}{query_url}"
        return result

    def _get(
        self, url: str,
        query_values: dict | None = None,
        stream: bool = False,
    ) -> requests.Response:
        url = self._build_url(url, query_values)

        def make_request() -> requests.Response:
            return requests.get(url, stream=stream, headers={
                "Authorization": f"Bearer {self.token}",
            }, timeout=self.DEFAULT_TIMEOUT)

        response = make_request()
        if response.status_code == 401:
            # Try refreshing token
            self._refresh_token()
            response = make_request()
        return response

    def _post(
        self, url: str,
        data: dict | None = None,
        stream: bool = False,
    ) -> requests.Response:
        url = self._build_url(url)

        def make_request() -> requests.Response:
            return requests.post(url, json=data, stream=stream, headers={
                "Authorization": f"Bearer {self.token}",
            }, timeout=self.DEFAULT_TIMEOUT)

        response = make_request()
        if response.status_code == 401:
            self._refresh_token()
            response = make_request()
        return response

    def _put(self, url: str, data: dict | None = None) -> None:
        pass

    def _delete(self, url: str, data: dict | None = None) -> None:
        pass

    @staticmethod
    def _read_json_list_stream(
        response: requests.Response,
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
                for obj in objects:
                    yield obj
                del objects[:]

    def prefix_remote_identifier(self, value: Any) -> str:
        return f"{self.remote_id}_{value}"

    def prefix_remote_name(self, value: Any) -> str:
        return f"({self.remote_id}) {value}"

    def get_datasets(self) -> dict | None:
        response = self._get("datasets")
        if response.status_code == 200:
            return cast(dict, response.json())
        return None

    def get_studies(self) -> dict | None:
        response = self._get("datasets/studies")
        if response.status_code == 200:
            return cast(dict, response.json())
        return None

    def get_dataset_config(self, study_id: str) -> dict | None:
        response = self._get(f"datasets/config/{study_id}")
        if response.status_code == 200:
            return cast(dict, response.json())
        return None

    def get_variants_preview(self, data: dict) -> requests.Response:
        response = self._post(
            "genotype_browser/preview/variants",
            data=data,
            stream=True,
        )
        return response

    def post_query_variants(
        self, data: dict, reduce_alleles: bool = False,
    ) -> Generator[Any, None, None]:
        """Post query request for variants preview."""
        assert data.get("download", False) is False
        data["reduceAlleles"] = reduce_alleles
        response = self._post(
            "genotype_browser/query",
            data=data,
            stream=True,
        )
        return self._read_json_list_stream(response)

    def post_query_variants_download(
        self, data: dict,
    ) -> Generator[Any, None, None]:
        """Post query request for variants download."""
        data["download"] = True
        response = self._post(
            "genotype_browser/query",
            data=data,
            stream=True,
        )
        return self._read_json_list_stream(response)

    def get_member_details(
        self, dataset_id: str, family_id: str, member_id: str,
    ) -> Any:
        """Get family member details."""
        response = self._get(
            f"families/{dataset_id}/{family_id}/members/{member_id}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_member_details(
        self, dataset_id: str, family_id: str,
    ) -> Any:
        """Get all family members details."""
        response = self._get(
            f"families/{dataset_id}/{family_id}/members/all",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_members(self, dataset_id: str, family_id: str) -> Any:
        """Get family members."""
        response = self._get(
            f"families/{dataset_id}/{family_id}/members",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_family_details(
        self, dataset_id: str, family_id: str,
    ) -> Any:
        """Get a family details."""
        response = self._get(
            f"families/{dataset_id}/{family_id}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_families(self, dataset_id: str) -> Any:
        """Get families in a dataset."""
        response = self._get(
            f"families/{dataset_id}",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_family_details(self, dataset_id: str) -> Any:
        """Get all families details of a dataset."""
        response = self._get(
            f"families/{dataset_id}/all",
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_person_set_collection_configs(self, dataset_id: str) -> Any:
        """Get person set collection configuration for a dataset."""
        response = self._get(f"person_sets/{dataset_id}/configs")

        if response.status_code != 200:
            return None

        return response.json()

    def get_common_report(
        self, common_report_id: str, full: bool = False,
    ) -> Any:
        """Get the commont report for a dataset."""
        if full:
            url = f"common_reports/studies/{common_report_id}/full"
        else:
            url = f"common_reports/studies/{common_report_id}"
        response = self._get(url)
        return response.json()

    def get_common_report_families_data(
        self, common_report_id: str,
    ) -> Any:
        """Get families part of the common report for a study."""
        response = self._post(
            f"common_reports/families_data/{common_report_id}",
            stream=True,
        )
        return response

    def get_pheno_browser_config(self, db_name: str) -> Any:
        """Get the pheno browser congigruation."""
        response = self._get(
            "pheno_browser/config",
            query_values={"db_name": db_name},
        )
        return response.json()

    def get_browser_measures_info(self, dataset_id: str) -> Any:
        """Get pheno browser measuers info for a dataset."""
        response = self._get(
            "pheno_browser/measures_info",
            query_values={"dataset_id": dataset_id},
        )
        return response.json()

    def get_browser_measures(
        self, dataset_id: str, instrument: str | None,
        search_term: str | None,
    ) -> Any:
        """Get pheno measures that correspond to a search."""
        response = self._get(
            "pheno_browser/measures",
            query_values={
                "dataset_id": dataset_id,
                "instrument": instrument,
                "search": search_term,
            },
            stream=True,
        )
        return self._read_json_list_stream(response)

    def get_instruments(self, dataset_id: str) -> Any:
        """Get instruments for a pheno measure."""
        response = self._get(
            "pheno_browser/instruments",
            query_values={"dataset_id": dataset_id},
        )
        return response.json()["instruments"]

    def get_measures_download(
            self, dataset_id: str,
            search_term: str | None = None,
            instrument: str | None = None,
    ) -> Any:
        """Post download request for pheno measures."""
        response = self._get(
            "pheno_browser/download",
            query_values={
                "dataset_id": dataset_id,
                "search_term": search_term,
                "instrument": instrument,
            },
            stream=True,
        )
        return response.iter_content()

    def post_enrichment_test(self, query: dict) -> Any:
        response = self._post(
            "enrichment/test",
            data=query,
        )
        return response.json()

    def get_instruments_details(self, dataset_id: str) -> Any:
        response = self._get(
            "pheno_tool/instruments",
            query_values={"datasetId": dataset_id},
        )

        return response.json()

    def get_measure(self, dataset_id: str, measure_id: str) -> Any:
        """Get a measure in a dataset."""
        response = self._get(
            "pheno_tool/measure",
            query_values={
                "datasetId": dataset_id,
                "measureId": measure_id,
            },
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measure_description(self, dataset_id: str, measure_id: str) -> Any:
        """Get a measure description."""
        response = self._get(
            "pheno_browser/measure_description",
            query_values={
                "dataset_id": dataset_id,
                "measure_id": measure_id,
            },
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measures(
        self, dataset_id: str,
        instrument_name: str | None,
        measure_type: str | None,
    ) -> Any:
        """Get measures for a dataset."""
        response = self._get(
            "pheno_tool/measures",
            query_values={
                "datasetId": dataset_id,
                "instrument": instrument_name,
                "measureType": measure_type,
            },
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_regressions(self, dataset_id: str) -> Any:
        """Get pheno measures regressions in a dataset."""
        response = self._get(
            "measures/regressions",
            query_values={
                "datasetId": dataset_id,
            },
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
        response = self._post(
            "pheno_tool/people_values",
            data=data,
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
        response = self._post(
            "pheno_tool",
            data=data,
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_gene_set_collections(self) -> Any:
        """Get gene set collections."""
        response = self._get(
            "gene_sets/gene_sets_collections",
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
        response = self._post(
            "gene_sets/gene_sets",
            data={"geneSetsCollection": collection_id},
        )

        if response.status_code != 200:
            return None

        return cast(List[Dict[str, Any]], response.json())

    def get_gene_set_download(
        self, gene_sets_collection: str, gene_set: str,
    ) -> Any:
        """Download a gene set."""
        response = self._get(
            "gene_sets/gene_set_download",
            query_values={
                "geneSetsCollection": gene_sets_collection,
                "geneSet": gene_set,
            },
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def has_denovo_gene_sets(self) -> bool:
        response = self._get("gene_sets/has_denovo")
        if response.status_code != 204:
            return False
        return True

    def get_denovo_gene_sets(self, gene_set_types: dict) -> Any:
        """Get denovo gene sets."""
        logger.debug(
            "getting denovo gene sets for: %s", gene_set_types)

        response = self._post(
            "gene_sets/gene_sets",
            data={
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
        response = self._post(
            "gene_sets/gene_set_download",
            data={
                "geneSetsCollection": "denovo",
                "geneSet": gene_set_id,
                "geneSetsTypes": gene_set_types,
            },
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def get_genomic_scores(self) -> list[dict[str, Any]] | None:
        response = self._get("genomic_scores/score_descs")
        if response.status_code != 200:
            return None
        return cast(list[dict[str, Any]], response.json())

    def get_genomic_score(self, score_id: str) -> dict[str, Any] | None:
        response = self._get(f"genomic_scores/score_descs/{score_id}")
        if response.status_code != 200:
            return None
        return cast(dict[str, Any], response.json()[0])

    def get_pheno_image(
        self, image_path: str,
    ) -> Tuple[bytes | None, str | None]:
        """
        Return tuple of image bytes and image type from remote.

        Accesses static files on the remote GPF instance.
        """
        url = self.build_image_url(image_path)
        response = requests.get(url, timeout=self.DEFAULT_TIMEOUT)
        if response.status_code != 200:
            return None, None

        return response.content, response.headers["content-type"]
