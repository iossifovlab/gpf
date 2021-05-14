import logging
from remote.rest_api_client import RESTClient, RESTClientRequestError
from studies.study_wrapper import RemoteStudyWrapper
from studies.remote_study import RemoteGenotypeData

logger = logging.getLogger(__name__)


class RemoteStudyDB:
    def __init__(self, remotes):
        self._remote_study_clients = dict()
        self._remote_study_ids = dict()
        self._remote_genotype_datas = dict()
        self._remote_study_wrappers = dict()

        if remotes is not None:
            for remote in remotes:
                logger.info(f"Creating remote {remote}")
                try:
                    client = RESTClient(
                        remote["id"],
                        remote["host"],
                        remote["user"],
                        remote["password"],
                        base_url=remote["base_url"],
                        port=remote.get("port", None),
                        protocol=remote.get("protocol", None),
                        gpf_prefix=remote.get("gpf_prefix", None)
                    )
                    self._fetch_remote_studies(client)
                except ConnectionError as err:
                    logger.error(err)
                    logger.error(f"Failed to create remote {remote['id']}")
                except RESTClientRequestError as err:
                    logger.error(err.message)

    def _fetch_remote_studies(self, rest_client):
        studies = rest_client.get_datasets()
        for study in studies["data"]:
            logger.info(f"creating remote genotype data: {study['id']}")
            rgd = RemoteGenotypeData(study["id"], rest_client)
            study_id = rgd.study_id
            self._remote_study_ids[study_id] = study["id"]
            self._remote_study_clients[study_id] = rest_client
            self._remote_genotype_datas[study_id] = rgd
            study_wrapper = RemoteStudyWrapper(rgd)
            self._remote_study_wrappers[study_id] = study_wrapper

    def has_remote_study_wrapper(self, study_id):
        return study_id in self._remote_study_wrappers.keys()

    def get_remote_study_wrapper(self, study_id):
        return self._remote_study_wrappers.get(study_id, None)

    def get_remote_study_wrappers(self):
        return self._remote_study_wrappers

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
