import logging
from typing import Any

from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework import status


from query_base.query_base import QueryDatasetView
from utils.expand_gene_set import expand_gene_set

LOGGER = logging.getLogger(__name__)


class EnrichmentModelsView(QueryDatasetView):
    """Select enrichment models view."""

    def get_from_config(
        self, dataset_id: str,
        property_name: str,
        selected: str
    ) -> list[dict[str, str]]:
        """Collect configuration values for a property."""
        enrichment_config = self.gpf_instance.get_study_enrichment_config(
            dataset_id
        )
        if enrichment_config is None:
            return []

        selected_properties = enrichment_config[selected]

        return [
            {"name": el.name, "desc": el.desc}
            for el in enrichment_config[property_name].values()
            if el.name in selected_properties
        ]

    def get(
        self, request: Request,  # pylint: disable=unused-argument
        dataset_id: str
    ) -> Response:
        """Return enrichment configuration prepared for choosing."""
        result = {
            "background": self.get_from_config(
                dataset_id, "background", "selected_background_values"
            ),
            "counting": self.get_from_config(
                dataset_id, "counting", "selected_counting_values"
            ),
        }
        return Response(result)


class EnrichmentTestView(QueryDatasetView):
    """View for running enrichment testing."""

    def __init__(self) -> None:
        super().__init__()
        self.gene_scores_db = self.gpf_instance.gene_scores_db

    @staticmethod
    def _parse_gene_syms(query: dict[str, Any]) -> set[str]:
        gene_syms = query.get("geneSymbols", None)
        if gene_syms is None:
            return set()

        if isinstance(gene_syms, str):
            gene_syms = gene_syms.split(",")
        return {g.strip() for g in gene_syms}

    def enrichment_description(self, query: dict[str, Any]) -> str:
        """Build enrichment result description."""
        gene_set = query.get("geneSet")
        if gene_set:
            desc = f"Gene Set: {gene_set}"
            return desc

        gene_score_request = query.get("geneScores", None)
        gene_scores_id = None
        if gene_score_request is not None:
            gene_scores_id = gene_score_request.get("score", None)
            range_start = gene_score_request.get("rangeStart", None)
            range_end = gene_score_request.get("rangeEnd", None)
        if gene_scores_id is not None and \
                gene_scores_id in self.gene_scores_db:
            if range_start is not None and range_end is not None:
                desc = (
                    f"Gene Scores: {gene_scores_id} "
                    f"from {range_start} up to {range_end}"
                )
            elif range_start is not None:
                desc = f"Gene Scores: {gene_scores_id} from {range_start}"
            elif range_end is not None:
                desc = f"Gene Scores: {gene_scores_id} up to {range_end}"
            else:
                desc = f"Gene Scores: {gene_scores_id}"
            return desc

        gene_syms = ",".join(self._parse_gene_syms(query))
        desc = f"Gene Symbols: {gene_syms}"
        return desc

    def post(self, request: Request) -> Response:
        """Run the enrichment test and return the result."""
        query = expand_gene_set(request.data, request.user)

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = None
        if "geneSymbols" in query:
            gene_syms = self._parse_gene_syms(query)
        else:
            gene_score_request = query.get("geneScores", None)
            if gene_score_request is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            gene_score_id = gene_score_request.get("score", None)
            range_start = gene_score_request.get("rangeStart", None)
            range_end = gene_score_request.get("rangeEnd", None)

            if gene_score_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if gene_score_id in self.gene_scores_db:
                score_desc = self.gpf_instance.get_gene_score_desc(
                    gene_score_id
                )
                gene_score = self.gene_scores_db.get_gene_score(
                    score_desc.resource_id
                )
                gene_syms = gene_score.get_genes(
                    gene_score_id,
                    score_min=range_start,
                    score_max=range_end
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        desc = self.enrichment_description(query)
        desc = f"{desc} ({len(gene_syms)})"

        background_name = query.get("enrichmentBackgroundModel", None)
        counting_name = query.get("enrichmentCountingModel", None)

        builder = self.gpf_instance.create_enrichment_builder(
            dataset_id, background_name, counting_name, gene_syms)

        if builder is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results = builder.build()

        enrichment = {"desc": desc, "result": results}
        return Response(enrichment)
