import logging
from typing import Any

from enrichment_api.enrichment_builder import BaseEnrichmentBuilder
from enrichment_api.enrichment_helper import BaseEnrichmentHelper
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import RemoteWDAEStudy
from rest_client.rest_client import RESTClient, RESTError

logger = logging.getLogger(__name__)


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


class RemoteEnrichmentBuilder(BaseEnrichmentBuilder):
    """Adapter for remote PhenoTool class."""

    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        super().__init__()
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, RemoteWDAEStudy):
            return None

        return RemoteEnrichmentBuilder(
            study.rest_client, study.remote_study_id)

    def enrichment_test(
        self,
        query: dict[str, Any],
    ) -> dict[str, Any]:
        """Build enrichment test result."""
        logger.info("Building enrichment with query: %s", query)
        query["datasetId"] = self.dataset_id
        try:
            result = self.rest_client.post_enrichment_test(query)

        except RESTError as e:
            raise ValueError(e) from e
        return {
            "desc": result.get("desc", ""),
            "result": result.get("result", []),
        }
