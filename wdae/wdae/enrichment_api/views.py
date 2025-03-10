import logging
from typing import Any, cast

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from utils.expand_gene_set import expand_gene_set

from dae.enrichment_tool.enrichment_helper import EnrichmentHelper
from dae.studies.study import GenotypeData

logger = logging.getLogger(__name__)


class EnrichmentModelsView(QueryBaseView):
    """Select enrichment models view."""

    def __init__(self) -> None:
        super().__init__()
        self.enrichment_helper = EnrichmentHelper(self.gpf_instance.grr)

    def _collect_counting_models(
        self, study: GenotypeData,
    ) -> list[dict[str, str]]:
        """Collect counting models."""
        enrichment_config = self.enrichment_helper.get_enrichment_config(study)
        if enrichment_config is None:
            return []

        selected_counting_models = (
            self.enrichment_helper.get_selected_counting_models(study)
        )

        return [
            {"id": counting_model.id,
             "name": counting_model.name,
             "desc": counting_model.desc}
            for counting_model in dict(enrichment_config["counting"]).values()
            if counting_model.id in selected_counting_models
        ]

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request, dataset_id: str) -> Response:
        """Return enrichment configuration prepared for choosing."""
        study = self.gpf_instance.get_genotype_data(dataset_id)

        if study is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        background_descriptions = []
        study_backgrounds = self.enrichment_helper \
            .collect_genotype_data_backgrounds(study)
        default_background_model = self.enrichment_helper \
            .get_default_background_model(study)
        default_counting_model = self.enrichment_helper \
            .get_default_counting_model(study)

        background_descriptions = [
            {"id": background.background_id,
             "name": background.name,
             "type": background.background_type,
             "summary": background.resource.get_summary(),
             "desc": background.resource.get_description()}
            for background in study_backgrounds
        ]

        return Response({
            "background": background_descriptions,
            "counting": self._collect_counting_models(study),
            "defaultBackground": default_background_model,
            "defaultCounting": default_counting_model,
        })


class EnrichmentTestView(QueryBaseView):
    """View for running enrichment testing."""

    def __init__(self) -> None:
        super().__init__()
        self.gene_scores_db = self.gpf_instance.gene_scores_db
        self.enrichment_helper = EnrichmentHelper(self.gpf_instance.grr)

    @staticmethod
    def _parse_gene_syms(query: dict[str, Any]) -> list[str]:
        gene_syms = query.get("geneSymbols")
        if gene_syms is None:
            return []

        if isinstance(gene_syms, str):
            gene_syms = gene_syms.split(",")
        return [g.strip() for g in gene_syms]

    def enrichment_description(self, query: dict[str, Any]) -> str:
        """Build enrichment result description."""
        gene_set = query.get("geneSet")
        if gene_set:
            return f"Gene Set: {gene_set}"

        gene_score_request = query.get("geneScores")
        gene_scores_id = None
        range_start = None
        range_end = None
        if gene_score_request is not None:
            gene_scores_id = gene_score_request.get("score", None)
            range_start = gene_score_request.get("rangeStart", None)
            range_end = gene_score_request.get("rangeEnd", None)
        if gene_scores_id is not None and \
                gene_scores_id in self.gene_scores_db:
            if range_start is not None and range_end is not None:
                desc = (
                    f"Gene Scores: {gene_scores_id} "
                    f"from {round(range_start, 2)} up to {round(range_end, 2)}"
                )
            elif range_start is not None:
                desc = (
                    f"Gene Scores: {gene_scores_id} "
                    f"from {round(range_start, 2)}"
                )
            elif range_end is not None:
                desc = (
                    f"Gene Scores: {gene_scores_id} "
                    f"up to {round(range_end, 2)}"
                )
            else:
                desc = f"Gene Scores: {gene_scores_id}"
            return desc

        gene_syms = ",".join(self._parse_gene_syms(query))
        return f"Gene Symbols: {gene_syms}"

    def post(self, request: Request) -> Response:
        """Run the enrichment test and return the result."""
        query = expand_gene_set(cast(dict, request.data))

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)
        assert dataset is not None

        builder = self.gpf_instance \
            .get_enrichment_builder(dataset)  # type: ignore

        if builder is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                    gene_score_id,
                )
                gene_score = self.gene_scores_db.get_gene_score(
                    score_desc.resource_id,
                )
                gene_syms = gene_score.get_genes(
                    gene_score_id,
                    score_min=range_start,
                    score_max=range_end,
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        desc = self.enrichment_description(query)
        desc = f"{desc} ({len(gene_syms)})"

        background_name = query.get("enrichmentBackgroundModel", None)
        counting_name = query.get("enrichmentCountingModel", None)
        logger.info("selected background model: %s", background_name)
        logger.info("selected counting model: %s", counting_name)

        results = builder.build(gene_syms, background_name, counting_name)
        return Response({"desc": desc, "result": results})
