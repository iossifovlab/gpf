import logging
from typing import List, Dict, Any, Optional, cast

import requests  # type: ignore
import ijson  # type: ignore


logger = logging.getLogger(__name__)


class RESTClientRequestError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RESTClient:

    def __init__(
            self, remote_id, host,
            username, password,
            base_url=None, port=None,
            protocol=None, gpf_prefix=None):
        self.host = host
        self.remote_id = remote_id
        self.username = username
        self.password = password
        if base_url:
            if not base_url.endswith("/"):
                base_url = f"{base_url}/"
            if not base_url.startswith("/"):
                base_url = f"/{base_url}"
            self.base_url = base_url
        else:
            self.base_url = "/"

        if port:
            self.port = port
        else:
            self.port = None

        if protocol:
            self.protocol = protocol
        else:
            self.protocol = "http"

        if gpf_prefix:
            self.gpf_prefix = gpf_prefix
        else:
            self.gpf_prefix = None

        self.session = self._login()

    def _login(self):
        login_url = "users/login"
        session = requests.session()
        data = {
            "username": self.username,
            "password": self.password
        }
        login_url = self._build_url(login_url)
        response = session.post(login_url, data=data)
        if response.status_code != 204:
            raise RESTClientRequestError(
                f"Failed to login when creating session for {self.remote_id}"
            )
        return session

    def build_host_url(self):
        if self.port:
            return f"{self.protocol}://{self.host}:{self.port}"
        else:
            return f"{self.protocol}://{self.host}"

    def build_api_base_url(self):
        host_url = self.build_host_url()
        if self.gpf_prefix:
            return f"{host_url}/{self.gpf_prefix}{self.base_url}"
        else:
            return f"{host_url}{self.base_url}"

    def _build_url(self, url, query_values=None):
        query_url = url
        if query_values:
            first = True
            for k, v in query_values.items():
                if v is None:
                    continue
                query_url += "?" if first else "&"
                query_url += f"{k}={v}"
                first = False
        base = self.build_api_base_url()
        result = f"{base}{query_url}"
        return result

    def _get(self, url, query_values=None, stream=False):
        url = self._build_url(url, query_values)
        response = self.session.get(url, stream=stream)
        return response

    def _post(self, url, data=None, stream=False):
        url = self._build_url(url)
        response = self.session.post(url, json=data, stream=stream)
        return response

    def _put(self, url, data=None):
        pass

    def _delete(self, url, data=None):
        pass

    def _read_json_list_stream(self, response, multiple_values=False):
        stream = response.iter_content()
        objects = ijson.sendable_list()
        coro = ijson.items_coro(
            objects, "item", use_float=True, multiple_values=False
        )
        for chunk in stream:
            coro.send(chunk)
            if len(objects):
                for o in objects:
                    yield o
                del objects[:]

    def prefix_remote_identifier(self, value):
        return f"{self.remote_id}_{value}"

    def prefix_remote_name(self, value):
        return f"({self.remote_id}) {value}"

    def get_datasets(self):
        response = self._get("datasets")
        print(response.content)
        if response.status_code == 200:
            return response.json()

    def get_dataset_config(self, study_id):
        response = self._get(f"datasets/config/{study_id}")
        print(response.content)
        if response.status_code == 200:
            return response.json()

    def get_variants_preview(self, data):
        response = self._post(
            "genotype_browser/preview/variants",
            data=data,
            stream=True
        )
        return response

    def post_query_variants(self, data, reduce_alleles=False):
        assert data.get("download", False) is False
        data["reduceAlleles"] = reduce_alleles
        response = self._post(
            "genotype_browser/query",
            data=data,
            stream=True
        )
        return self._read_json_list_stream(response)

    def post_query_variants_download(self, data):
        data["download"] = True
        response = self._post(
            "genotype_browser/query",
            data=data,
            stream=True
        )
        return self._read_json_list_stream(response)

    def get_common_report(self, common_report_id, full=False):
        if full:
            url = f"common_reports/studies/{common_report_id}/full"
        else:
            url = f"common_reports/studies/{common_report_id}"
        response = self._get(url)
        return response.json()

    def get_common_report_families_data(self, common_report_id):
        response = self._get(
            f"common_reports/families_data/{common_report_id}",
            stream=True
        )
        print(response.content)
        return response

    def get_pheno_browser_config(self, db_name):
        response = self._get(
            "pheno_browser/config",
            query_values={"db_name": db_name},
        )
        print(response.content)
        return response.json()

    def get_browser_measures_info(self, dataset_id):
        response = self._get(
            "pheno_browser/measures_info",
            query_values={"dataset_id": dataset_id}
        )
        print(response.content)

        return response.json()

    def get_browser_measures(self, dataset_id, instrument, search_term):
        response = self._get(
            "pheno_browser/measures",
            query_values={
                "dataset_id": dataset_id,
                "instrument": instrument,
                "search": search_term
            },
            stream=True
        )
        return self._read_json_list_stream(response)

    def get_instruments(self, dataset_id):
        response = self._get(
            "pheno_browser/instruments",
            query_values={"dataset_id": dataset_id},
        )
        print(response.content)
        return response.json()["instruments"]

    def post_measures_download(
            self, dataset_id, measure_ids=None, instrument=None
    ):
        response = self._post(
            "pheno_browser/download",
            data={
                "dataset_id": dataset_id,
                "measures": measure_ids,
                "instrument": instrument,
            },
            stream=True
        )
        return response.iter_content()

    def post_enrichment_test(self, query):
        response = self._post(
            "enrichment/test",
            data=query,
        )
        return response.json()

    def post_pheno_persons(
            self, dataset_id, measure_ids, roles, person_ids, family_ids):
        data = {
            "datasetId": dataset_id,
            "measureIds": measure_ids,
            "roles": roles,
            "personIds": person_ids,
            "familyIds": family_ids,
        }
        response = self._post(
            "pheno_tool/persons",
            data=data
        )
        return response.json()

    def post_pheno_persons_values(
            self, dataset_id, measure_ids, roles, person_ids, family_ids):
        data = {
            "datasetId": dataset_id,
            "measureIds": measure_ids,
            "roles": roles,
            "personIds": person_ids,
            "familyIds": family_ids,
        }
        response = self._post(
            "pheno_tool/persons_values",
            data=data
        )
        return response.json()

    def get_instruments_details(self, dataset_id):
        response = self._get(
            "pheno_tool/instruments",
            query_values={"datasetId": dataset_id}
        )

        return response.json()

    def get_measure(self, dataset_id, measure_id):
        response = self._get(
            "pheno_tool/measure",
            query_values={
                "datasetId": dataset_id,
                "measureId": measure_id,
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measure_description(self, dataset_id, measure_id):
        response = self._get(
            "pheno_browser/measure_description",
            query_values={
                "dataset_id": dataset_id,
                "measure_id": measure_id,
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_measures(self, dataset_id, instrument_name, measure_type):
        response = self._get(
            "pheno_tool/measures",
            query_values={
                "datasetId": dataset_id,
                "instrument": instrument_name,
                "measureType": measure_type,
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_regressions(self, dataset_id):
        response = self._get(
            "measures/regressions",
            query_values={
                "datasetId": dataset_id
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    def post_measure_values(
            self, dataset_id, measure_id, person_ids,
            family_ids, roles, default_filter):
        data = {
            "datasetId": dataset_id,
            "measureId": measure_id,
            "personIds": person_ids,
            "familyIds": family_ids,
            "roles": roles,
            "defaultFilter": default_filter
        }
        response = self._post(
            "pheno_tool/measure_values",
            data=data
        )

        return response.json()

    def post_pheno_values(
            self, dataset_id, measure_ids, person_ids,
            family_ids, roles, default_filter):
        data = {
            "datasetId": dataset_id,
            "measureIds": measure_ids,
            "personIds": person_ids,
            "familyIds": family_ids,
            "roles": roles,
            "defaultFilter": default_filter
        }
        response = self._post(
            "pheno_tool/values",
            data=data
        )

        return response.json()

    def post_instrument_values(
            self, dataset_id, instrument_name,
            person_ids, family_ids, roles, measures):
        data = {
            "datasetId": dataset_id,
            "instrumentName": instrument_name,
            "personIds": person_ids,
            "familyIds": family_ids,
            "roles": roles,
            "measures": measures,
        }

        response = self._post(
            "pheno_tool/instrument_values",
            data=data
        )
        return response.json()

    def post_pheno_tool(self, data):
        response = self._post(
            "pheno_tool",
            data=data
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_gene_set_collections(self):
        response = self._get(
            "gene_sets/gene_sets_collections"
        )

        if response.status_code != 200:
            logger.warning(
                f"error while looking for gene sets collections; "
                f"{response.status_code}: ({response})")
            return []

        return response.json()

    def get_gene_sets(self, collection_id) -> Optional[List[Dict[str, Any]]]:
        response = self._post(
            "gene_sets/gene_sets",
            data={"geneSetsCollection": collection_id}
        )

        if response.status_code != 200:
            return None

        return cast(List[Dict[str, Any]], response.json())

    def get_gene_set_download(self, gene_sets_collection, gene_set):
        response = self._get(
            "gene_sets/gene_set_download",
            query_values={
                "geneSetsCollection": gene_sets_collection,
                "geneSet": gene_set,
            }
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def has_denovo_gene_sets(self):
        response = self._get("gene_sets/has_denovo")
        if response.status_code != 204:
            return False
        return True

    def get_denovo_gene_sets(self, gene_set_types):
        logger.debug(
            f"getting denovo gene sets for: {gene_set_types}")

        response = self._post(
            "gene_sets/gene_sets",
            data={
                "geneSetsCollection": "denovo",
                "geneSetsTypes": gene_set_types
            }
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_denovo_gene_set(self, gene_set_id, gene_set_types):
        response = self._post(
            "gene_sets/gene_set_download",
            data={
                "geneSetsCollection": "denovo",
                "geneSet": gene_set_id,
                "geneSetsTypes": gene_set_types
            }
        )

        if response.status_code != 200:
            return None

        return response.content.decode()

    def get_member_details(self, dataset_id, family_id, member_id):
        response = self._get(
            f"families/{dataset_id}/{family_id}/members/{member_id}"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_member_details(self, dataset_id, family_id):
        response = self._get(
            f"families/{dataset_id}/{family_id}/members/all"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_members(self, dataset_id, family_id):
        response = self._get(
            f"families/{dataset_id}/{family_id}/members"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_family_details(self, dataset_id, family_id):
        response = self._get(
            f"families/{dataset_id}/{family_id}"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_families(self, dataset_id):
        response = self._get(
            f"families/{dataset_id}"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_all_family_details(self, dataset_id):
        response = self._get(
            f"families/{dataset_id}/all"
        )

        if response.status_code != 200:
            return None

        return response.json()

    def get_person_set_collection_configs(self, dataset_id):
        response = self._get(f"person_sets/{dataset_id}/configs")

        if response.status_code != 200:
            return None

        return response.json()
