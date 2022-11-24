"""Provides class for handling of remote studies."""

import logging
from typing import List, Dict
from remote.rest_api_client import RESTClient, RESTClientRequestError
from studies.remote_study import RemoteGenotypeData
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class RemoteStudyDB:
    """Class to manage remote studies."""

    def __init__(self, clients: List[RESTClient]):
        self.remote_study_clients: Dict[str, RESTClient] = {}
        self.remote_study_ids: Dict[str, str] = {}
        self.remote_genotype_data: Dict[str, GenotypeData] = {}

        for client in clients:
            try:
                self._fetch_remote_studies(client)
            except RESTClientRequestError as err:
                logger.error(err.message)

    def add_client(self, rest_client: RESTClient) -> None:
        self._fetch_remote_studies(rest_client)

    def _fetch_remote_studies(self, rest_client: RESTClient):
        studies = rest_client.get_studies()
        if studies is None:
            raise RESTClientRequestError(
                f"Failed to get studies from {rest_client.remote_id}"
            )
        for study in studies["data"]:
            logger.info("creating remote genotype data: %s", study["id"])
            rgd = RemoteGenotypeData(study["id"], rest_client)
            study_id = rgd.study_id
            self.remote_study_ids[study_id] = study["id"]
            self.remote_study_clients[study_id] = rest_client
            self.remote_genotype_data[study_id] = rgd

    def get_genotype_data(self, study_id):
        return self.remote_genotype_data.get(study_id)

    def get_genotype_data_config(self, study_id):
        rgd = self.remote_genotype_data.get(study_id)
        if rgd is not None:
            return rgd.config
        return None

    def get_genotype_data_ids(self):
        return self.remote_genotype_data.keys()

    def get_all_genotype_datas(self):
        return [
            self.get_genotype_data(study_id)
            for study_id in self.get_genotype_data_ids()
        ]

    def get_all_genotype_data_configs(self):
        return [
            self.get_genotype_data_config(study_id)
            for study_id in self.get_genotype_data_ids()
        ]
