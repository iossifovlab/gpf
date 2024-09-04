from collections.abc import Iterable
from typing import Any, cast

from dae.enrichment_tool.enrichment_builder import BaseEnrichmentBuilder
from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from federation.remote.remote_study import RemoteGenotypeData
from federation.remote.remote_study_wrapper import RemoteStudyWrapper
from federation.remote.rest_api_client import RESTClient


class RemoteEnrichmentBuilder(BaseEnrichmentBuilder):
    """Builder for enrichment tool test for remote dataset."""

    def __init__(
        self, enrichment_helper: EnrichmentHelper,
        dataset: RemoteGenotypeData | RemoteStudyWrapper,
        client: RESTClient,
    ):
        super().__init__(enrichment_helper, dataset)
        self.client = client

    def build(
        self, gene_syms: Iterable[str],
        background_id: str | None, counting_id: str | None,
    ) -> list[dict[str, Any]]:

        query: dict[str, Any] = {}
        query["datasetId"] = self.dataset.remote_study_id
        query["geneSymbols"] = list(gene_syms)
        query["enrichmentBackgroundModel"] = background_id
        query["enrichmentCountingModel"] = counting_id

        return cast(
            list[dict[str, Any]],
            self.client.post_enrichment_test(self.query)["result"],
        )
