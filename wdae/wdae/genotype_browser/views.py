"""Genotype browser routes for browsing and listing variants in studies."""
import itertools
import logging
from typing import Any, cast

from dae.utils.dae_utils import join_line
from datasets_api.permissions import (
    handle_partial_permissions,
    user_has_permission,
)
from django.http.response import FileResponse, StreamingHttpResponse
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEStudy
from utils.expand_gene_set import expand_gene_set, expand_gene_syms
from utils.logger import request_logging
from utils.query_params import parse_query_params
from utils.streaming_response_util import iterator_to_json

logger = logging.getLogger(__name__)


class GenotypeBrowserQueryView(QueryBaseView, DatasetAccessRightsView):
    """Genotype browser queries view."""

    MAX_SHOWN_VARIANTS = 1000

    @request_logging(logger)
    def post(
        self, request: Request,
    ) -> StreamingHttpResponse | FileResponse | Response:
        """
        Query for variants from a dataset.

        Request:
            POST /genotype_browser/preview/variants HTTP/1.1
            Host: example.com
            Content-Type: application/json
            Accept: text/event-stream

            {
              "datasetId": "iossifov_2014",
              "maxVariantsCount": 1000
            }

        Response:
            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: text/event-stream
            [

            [col1,col2,col3,col4.....]

            ,

            [col1,col2,col3,col4.....]

            ,
            ......

            ,

            [col1,col2,col3,col4.....]

            ]

        Status codes:
            200: Successfully fetched variants
            403: User has no permissions for dataset
            400: Invalid request body
            404: Dataset does not exist

        Request JSON parameters:
            datasetId (string): ID of the dataset to query.
            download (boolean): Change response type for easier download.
            genomicScores (json): Genomic score range filter.
            maxVariantsCount (integer): Maximum amount of variants to query.
            sources (list): List of name-source objects: columns to fetch.
            summaryVariantIds (list): List of summary variant IDs for filter.
            querySummary (boolean): True if should query only summary variants.
            uniqueFamilyVariants (boolean): Query for unique variants only.
            regions (list): List of regions as strings to filter with.
            presentInChild (json): Roles object to filter with.
            presentInParent (json): Roles object to filter with.
            inheritanceTypeFilter (list): Inheritance filtering.
            geneScores (list): Gene score range filter.
            genders (list): Gender filter.
            variantTypes (list): Filter by variant type.
            effectTypes (list): Filter by effect type.
            studyFilters (list): Filter by study ID (dataset only).
            personFilters (list): Filter with person filters.
            familyFilters (list): Filter with family filters.
            personIds (list): Filter by person IDs.
            familyTypes (list): Filter by family type.
            familyIds (list): Filter by family IDs.
            affectedStatus (list): Filter by affected status.
            tagIntersection (boolean): Change Family tags interesection mode
            selectedFamilyTags (list): Family tags to include
            deselectedFamilyTags (list): Family tags to exlude
        """
        # pylint: disable=too-many-branches
        logger.info("query v3 variants request: %s", str(request.data))
        data = cast(dict[str, Any], request.data)
        user = request.user

        if not isinstance(data, dict):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if "queryData" in data:
            data = cast(dict[str, Any], parse_query_params(data))

        dataset_id = data.get("datasetId", None)

        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not user_has_permission(self.instance_id, request.user, dataset_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if "genomicScores" in data:
            scores = cast(list[dict[str, Any]], data["genomicScores"])
            for score in scores:
                if score.get("rangeStart") is None \
                    and score.get("rangeEnd") is None \
                    and score.get("values") is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        is_download = cast(bool, data.pop("download", False))

        if "maxVariantsCount" in data:
            max_variants = cast(int, data["maxVariantsCount"])
        else:
            if is_download:
                max_variants = 10000
                if not user.is_anonymous and \
                        (user.is_staff or user.has_unlimited_download):
                    max_variants = None
            else:
                max_variants = self.MAX_SHOWN_VARIANTS + 1

        if max_variants == -1:
            # unlimited variants preview
            max_variants = None

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = cast(WDAEStudy, dataset)

        if not dataset.genotype_data.is_remote:
            data = expand_gene_set(data)
        elif "geneSet" in data:
            gene_set = expand_gene_syms(data)
            data["geneSymbols"] = list(gene_set["syms"])
            del data["geneSet"]

        if "sources" in data:
            sources = data.pop("sources")
        else:
            # TODO Handle summary variant preview and download sources

            study_config = dataset.genotype_data.config
            if is_download:
                cols = study_config.genotype_browser.download_columns
            else:
                cols = study_config.genotype_browser.preview_columns
            sources = WDAEStudy.get_columns_as_sources(
                dataset.genotype_data.config, cols,
            )

        if not isinstance(sources, list):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        handle_partial_permissions(self.instance_id, user, dataset_id, data)

        response: FileResponse | StreamingHttpResponse | None = None
        result = dataset.query_variants_wdae(
            data, sources,
            self.query_transformer,
            self.response_transformer,
            max_variants_count=max_variants,
            max_variants_message=is_download,
        )
        if is_download:
            columns = [s.get("name", s["source"]) for s in sources]
            result = map(
                join_line, itertools.chain([columns], filter(None, result)))  # type: ignore
            response = FileResponse(
                result, filename="variants.tsv",
                as_attachment=True, content_type="text/tsv",
            )
            response["Content-Disposition"] = \
                "attachment; filename=variants.tsv"
            response["Expires"] = "0"
        else:
            response = StreamingHttpResponse(
                iterator_to_json(result),
                status=status.HTTP_200_OK,
                content_type="text/event-stream",
            )

        response["Cache-Control"] = "no-cache"
        return response
