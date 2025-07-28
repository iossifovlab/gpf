import logging
from typing import cast

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from gpf_instance.gpf_instance import WGPFInstance
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy

from enrichment_api.enrichment_builder import (
    BaseEnrichmentBuilder,
    EnrichmentBuilder,
)
from enrichment_api.enrichment_helper import (
    BaseEnrichmentHelper,
    EnrichmentHelper,
)

logger = logging.getLogger(__name__)


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
            study,
        )

        return Response(enrichment_helper.get_enrichment_models())


class EnrichmentTestView(QueryBaseView):
    """View for running enrichment testing."""

    def __init__(self) -> None:
        super().__init__()
        self.gene_scores_db = self.gpf_instance.gene_scores_db

    def post(self, request: Request) -> Response:
        """Run the enrichment test and return the result."""
        query = cast(dict, request.data)

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)
        assert dataset is not None

        builder = create_enrichment_builder(self.gpf_instance, dataset)

        if builder is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            result = builder.enrichment_test(query)
        except ValueError as e:
            logger.exception("Enrichment test failed")
            if str(e).isdigit():
                return Response(status=int(str(e)))
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


def create_enrichment_helper(
    gpf_instance: WGPFInstance, study: WDAEAbstractStudy,
) -> BaseEnrichmentHelper:
    """Create an enrichment builder for the given dataset."""
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
    gpf_instance: WGPFInstance, study: WDAEAbstractStudy,
) -> BaseEnrichmentBuilder:
    """Create an enrichment builder for the given dataset."""
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
        gpf_instance.gene_scores_db,
        study,
    )
