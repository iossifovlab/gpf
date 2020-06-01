from dae.studies.study_wrapper import StudyWrapperBase
from dae.remote.rest_api_client import RESTClient


class RemoteStudyWrapper(StudyWrapperBase):

    def __init__(self, study, host, base_url, port):
        self.rest_client = RESTClient(host, base_url=base_url, port=port)
        self.study = study
        self.config = self.rest_client.get_dataset_config(self.study)

    def get_variants_wdae_preview(self, query, max_variants_count=10000):
        query["datasetId"] = self.study
        return iter(self.rest_client.get_variants_preview(query).json())

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        raise NotImplementedError


# rsw = RemoteStudyWrapper("AGRE_WG_859", "localhost", "api/v3", 8000)
# print(rsw.config)
# response = rsw.get_variants_wdae_preview(dict())
# print(response.status_code)
# print(response.headers)
# # print(response.content)
# print(response.json())
