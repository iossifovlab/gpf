import logging
from typing import Any, cast

from enrichment_api.enrichment_builder import BaseEnrichmentBuilder
from enrichment_api.enrichment_helper import BaseEnrichmentHelper
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import RemoteWDAEStudy
from rest_client.rest_client import RESTClient

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
        gene_syms: list[str] | None,
        gene_score: dict[str, Any] | None,
        background_id: str | None,
        counting_id: str | None,
        gene_set_id: str | None,
    ) -> dict[str, Any]:
        """Build enrichment test result."""
        query: dict[str, Any] = {}
        query["datasetId"] = self.dataset_id

        if gene_syms:
            query["geneSymbols"] = list(gene_syms)
        if gene_score:
            query["geneScores"] = gene_score
        if background_id:
            query["enrichmentBackgroundModel"] = background_id
        if counting_id:
            query["enrichmentCountingModel"] = counting_id
        if gene_set_id:
            query["geneSet"] = {
                "geneSet": {
                    "desc": gene_set_id
                },
                "geneSetsTypes": [],
            }

        logger.info("Building enrichment with query: %s", query)
        result = self.rest_client.post_enrichment_test(query)
        if result is None:
            return {}
        return {
            "desc": result.get("results", ""),
            "result": cast(list[dict[str, Any]], result.get("results", [])),
        }
