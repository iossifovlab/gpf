"""Provides class for handling of remote studies."""

import logging
from typing import Dict, Optional

from box import Box
from remote.rest_api_client import RESTClient, RESTClientRequestError

from studies.remote_study import RemoteGenotypeData

logger = logging.getLogger(__name__)


class RemoteStudyDB:
    """Class to manage remote studies."""

    def __init__(self, clients: Dict[str, RESTClient]) -> None:
        self.remote_study_clients: Dict[str, RESTClient] = {}
        self.remote_study_ids: Dict[str, str] = {}
        self.remote_genotype_data: Dict[str, RemoteGenotypeData] = {}

        for client in clients.values():
            try:
                self._fetch_remote_studies(client)
            except RESTClientRequestError as err:
                logger.error(err.message)

    def add_client(self, rest_client: RESTClient) -> None:
        self._fetch_remote_studies(rest_client)

    def _fetch_remote_studies(self, rest_client: RESTClient) -> None:
        studies = rest_client.get_studies()
        if studies is None:
            raise RESTClientRequestError(
                f"Failed to get studies from {rest_client.remote_id}",
            )
        for study in studies["data"]:
            logger.info("creating remote genotype data: %s", study["id"])
            rgd = RemoteGenotypeData(study["id"], rest_client)
            study_id = rgd.study_id
            self.remote_study_ids[study_id] = study["id"]
            self.remote_study_clients[study_id] = rest_client
            self.remote_genotype_data[study_id] = rgd

    def get_genotype_data(self, study_id: str) -> Optional[RemoteGenotypeData]:
        return self.remote_genotype_data.get(study_id)

    def get_genotype_data_config(self, study_id: str) -> Optional[Box]:
        rgd = self.remote_genotype_data.get(study_id)
        if rgd is not None:
            return rgd.config
        return None

    def get_genotype_data_ids(self) -> list[str]:
        return list(self.remote_genotype_data.keys())

    def get_all_genotype_datas(self) -> list[RemoteGenotypeData]:
        result = []
        for study_id in self.get_genotype_data_ids():
            study = self.get_genotype_data(study_id)
            if study is not None:
                result.append(study)
        return result

    def get_all_genotype_data_configs(self) -> list[Box]:
        result = []
        for study_id in self.get_genotype_data_ids():
            config = self.get_genotype_data_config(study_id)
            if config is not None:
                result.append(config)
        return result
