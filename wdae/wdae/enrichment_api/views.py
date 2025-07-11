import logging
from typing import Any, cast

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from gpf_instance.gpf_instance import WGPFInstance
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEStudy
from utils.expand_gene_set import expand_gene_set

from enrichment_api.enrichment_builder import (
    BaseEnrichmentBuilder,
    EnrichmentBuilder,
)
from enrichment_api.enrichment_helper import (
    BaseEnrichmentHelper,
    EnrichmentHelper,
)


class EnrichmentModelsView(QueryBaseView):
    """Select enrichment models view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request, dataset_id: str) -> Response:
        """Return enrichment configuration prepared for choosing."""
        study = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if study is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        enrichment_helper = create_enrichment_helper(
            self.gpf_instance,
            study.study_id,
        )

        return Response(enrichment_helper.get_enrichment_models())


class EnrichmentTestView(QueryBaseView):
    """View for running enrichment testing."""

    def __init__(self) -> None:
        super().__init__()
        self.gene_scores_db = self.gpf_instance.gene_scores_db

    @staticmethod
    def _parse_gene_syms(query: dict[str, Any]) -> list[str]:
        gene_syms = query.get("geneSymbols")
        if gene_syms is None:
            return []

        if isinstance(gene_syms, str):
            gene_syms = gene_syms.split(",")
        return [g.strip() for g in gene_syms]

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

        builder = create_enrichment_builder(self.gpf_instance, dataset.study_id)

        if builder is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if "geneSymbols" not in query and (
            "geneScores" not in query
            or (
                "geneScores" in query
                and "score" not in query.get("geneScores", {})
            )
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        gene_syms = None
        if "geneSymbols" in query:
            gene_syms = self._parse_gene_syms(query)

        gene_scores = cast(dict[str, Any] | None, query.get("geneScores", None))

        try:
            desc = builder.create_enrichment_description(
                cast(str, query.get("geneSet")),
                gene_scores,
                gene_syms,
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            results = builder.build(
                gene_syms,
                gene_scores,
                query.get("enrichmentBackgroundModel", None),
                query.get("enrichmentCountingModel", None),
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({"desc": desc, "result": results})


def create_enrichment_helper(
    gpf_instance: WGPFInstance, study_id: str,
) -> BaseEnrichmentHelper:
    """Create an enrichment builder for the given dataset."""
    study = gpf_instance.get_wdae_wrapper(study_id)
    if study is None:
        raise ValueError(
            f"Dataset {study_id} not found! Cannot create enrichment helper.",
        )
    for ext_name, extension in gpf_instance.extensions.items():
        enrichment_helper = extension.get_tool(study, "enrichment_helper")
        if enrichment_helper is not None:
            if not isinstance(enrichment_helper, BaseEnrichmentHelper):
                raise ValueError(
                    f"{ext_name} returned an invalid enrichment helper!")
            return enrichment_helper

    if not isinstance(study, WDAEStudy):
        raise ValueError(  # noqa: TRY004
            f"Enrichment helper for {study.study_id} is missing!")

    return EnrichmentHelper(gpf_instance.grr, study)


def create_enrichment_builder(
    gpf_instance: WGPFInstance, study_id: str,
) -> BaseEnrichmentBuilder:
    """Create an enrichment builder for the given dataset."""
    study = gpf_instance.get_wdae_wrapper(study_id)
    if study is None:
        raise ValueError(
            f"Dataset {study_id} not found! Cannot create enrichment builder.",
        )
    for ext_name, extension in gpf_instance.extensions.items():
        enrichment_builder = extension.get_tool(study, "enrichment_builder")
        if enrichment_builder is not None:
            if not isinstance(enrichment_builder, BaseEnrichmentBuilder):
                raise ValueError(
                    f"{ext_name} returned an invalid enrichment builder!")
            return enrichment_builder

    if not isinstance(study, WDAEStudy):
        raise ValueError(  # noqa: TRY004
            f"Enrichment helper for {study.study_id} is missing!")
    return EnrichmentBuilder(
        EnrichmentHelper(gpf_instance.grr, study),
        study,
    )
