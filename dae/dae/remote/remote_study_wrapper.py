from dae.studies.study_wrapper import StudyWrapperBase
from dae.remote.remote_phenotype_data import RemotePhenotypeData
import json

from dae.configuration.gpf_config_parser import FrozenBox


class RemoteStudyWrapper(StudyWrapperBase):

    def __init__(self, study_id, rest_client):
        self._remote_study_id = study_id
        self.rest_client = rest_client
        self.study_id = self.rest_client.get_remote_dataset_id(study_id)
        config = self.rest_client.get_dataset_config(self._remote_study_id)
        config["id"] = self.study_id
        config["name"] = self.study_id
        del config["access_rights"]
        del config["groups"]
        self.config = FrozenBox(config)

        self.phenotype_data = RemotePhenotypeData(
            self._remote_study_id,
            self.rest_client
        )

        self.is_remote = True

    def get_wdae_preview_info(self, query, max_variants_count=10000):
        query["datasetId"] = self._remote_study_id
        return self.rest_client.get_browser_preview_info(query).json()

    def get_variants_wdae_preview(self, query, max_variants_count=10000):
        query["datasetId"] = self._remote_study_id
        response = self.rest_client.get_variants_preview(query)
        for line in response.iter_lines():
            if line:
                variants = json.loads(line)
                for variant in variants:
                    yield variant

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_genotype_data_group_description(self):
        return self.config.to_dict()


# rsw = RemoteStudyWrapper("AGRE_WG_859", "localhost", "api/v3", 8000)
# print(rsw.config)
# response = rsw.get_variants_wdae_preview(dict())
# print(response.status_code)
# print(response.headers)
# # print(response.content)
# print(response.json())
