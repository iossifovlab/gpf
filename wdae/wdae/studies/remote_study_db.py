import logging
from typing import List, Dict
from remote.rest_api_client import RESTClient, RESTClientRequestError
from studies.remote_study import RemoteGenotypeData

logger = logging.getLogger(__name__)


class RemoteStudyDB:
    def __init__(self, clients: List[RESTClient]):
        self._remote_study_clients: Dict[str, RESTClient] = dict()
        self._remote_study_ids = dict()
        self._remote_genotype_datas = dict()

        for client in clients:
            try:
                self._fetch_remote_studies(client)
            except RESTClientRequestError as err:
                logger.error(err.message)

    def _fetch_remote_studies(self, rest_client):
        studies = rest_client.get_datasets()
        if studies is None:
            raise RESTClientRequestError(
                f"Failed to get studies from {rest_client.remote_id}"
            )
        for study in studies["data"]:
            logger.info(f"creating remote genotype data: {study['id']}")
            rgd = RemoteGenotypeData(study["id"], rest_client)
            study_id = rgd.study_id
            self._remote_study_ids[study_id] = study["id"]
            self._remote_study_clients[study_id] = rest_client
            self._remote_genotype_datas[study_id] = rgd

    def get_genotype_data(self, study_id):
        return self._remote_genotype_datas.get(study_id)

    def get_genotype_data_config(self, study_id):
        rgd = self._remote_genotype_datas.get(study_id)
        if rgd is not None:
            return rgd.config
        return None

    def get_genotype_data_ids(self):
        return self._remote_genotype_datas.keys()

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
