from typing import Any

from enrichment_api.enrichment_helper import BaseEnrichmentHelper
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import RemoteWDAEStudy
from federation.rest_api_client import RESTClient


class RemoteEnrichmentHelper(BaseEnrichmentHelper):
    """Adapter for remote PhenoTool class."""

    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        super().__init__()
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, RemoteWDAEStudy):
            return None

        return RemoteEnrichmentHelper(study.rest_client, study.remote_study_id)

    def get_enrichment_models(self) -> dict[str, Any]:
        return self.rest_client.get_enrichment_models(self.dataset_id)
