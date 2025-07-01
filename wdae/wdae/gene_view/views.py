import logging
from collections.abc import Generator

from datasets_api.permissions import get_permissions_etag
from django.contrib.auth.models import User
from django.http.response import FileResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import WDAEStudy
from utils.expand_gene_set import expand_gene_set
from utils.logger import request_logging
from utils.query_params import parse_query_params

LOGGER = logging.getLogger(__name__)


class ConfigView(QueryBaseView, DatasetAccessRightsView):
    """Gene browser config view."""

    @request_logging(LOGGER)
    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        """Get gene browser config."""
        data = expand_gene_set(request.query_params)
        dataset_id = data["datasetId"]
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(dataset.genotype_data.config["gene_browser"],
                        status=status.HTTP_200_OK)


class QueryVariantsView(QueryBaseView):
    """Gene view summary variants view."""
    @request_logging(LOGGER)
    @method_decorator(etag(get_permissions_etag))
    def post(self, request: Request) -> Response:
        """Query gene view summary variants."""
        data = expand_gene_set(request.data)  # pyright: ignore
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if dataset.genotype_data.is_remote:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        freq_col = \
            dataset.genotype_data.config["gene_browser"]["frequency_column"]

        return Response(list(
            dataset.get_gene_view_summary_variants(
                freq_col, self.query_transformer,
                self.response_transformer, **data,
            ),
        ))


class DownloadSummaryVariantsView(QueryBaseView):
    """Summary download view."""

    DOWNLOAD_LIMIT = 10000

    def generate_variants(
        self,
        data: dict,
        user: User,
        dataset: WDAEStudy,
    ) -> Generator[str, None, None]:
        """Summary variants generator."""
        # Return a response instantly and make download more responsive
        yield ""

        download_limit = None
        if not (
            user.is_authenticated and
            user.has_unlimited_download  # type: ignore
        ):
            download_limit = self.DOWNLOAD_LIMIT
        data.update({"limit": download_limit})

        freq_col = dataset.config["gene_browser"]["frequency_column"]
        yield from dataset.get_gene_view_summary_variants_download(
            freq_col,
            self.query_transformer,
            self.response_transformer,
            **data,
        )

    @request_logging(LOGGER)
    def post(self, request: Request) -> Response | FileResponse:
        """Summary variants download."""
        data = expand_gene_set(parse_query_params(request.data))
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if dataset.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if dataset.genotype_data.is_remote:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        response = FileResponse(
            self.generate_variants(data, request.user, dataset),
            content_type="text/tsv",
        )
        response["Content-Disposition"] = \
            "attachment; filename=summary_variants.tsv"
        response["Expires"] = "0"
        return response
