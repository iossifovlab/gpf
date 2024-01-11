from typing import Generator, cast
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.http.response import FileResponse
from django.contrib.auth.models import User
from query_base.query_base import QueryDatasetView
from studies.study_wrapper import StudyWrapper
from utils.logger import request_logging
from utils.query_params import parse_query_params
from utils.expand_gene_set import expand_gene_set

from datasets_api.permissions import \
    handle_partial_permissions


LOGGER = logging.getLogger(__name__)


class ConfigView(QueryDatasetView):
    @request_logging(LOGGER)
    def get(self, request):
        data = expand_gene_set(request.query_params, request.user)
        dataset_id = data["datasetId"]
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # LOGGER.info('dataset ' + str(dataset))
        config = dataset.config.gene_browser

        return Response(config, status=status.HTTP_200_OK)


class QueryVariantsView(QueryDatasetView):
    @request_logging(LOGGER)
    def post(self, request):
        data = expand_gene_set(request.data, request.user)
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if dataset.is_remote:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = cast(StudyWrapper, dataset)

        user = request.user
        handle_partial_permissions(self.instance_id, user, dataset_id, data)

        config = dataset.config.gene_browser
        freq_col = config.frequency_column

        return Response(
            list(dataset.get_gene_view_summary_variants(freq_col, **data))
        )


class DownloadSummaryVariantsView(QueryDatasetView):
    """Summary download view."""

    DOWNLOAD_LIMIT = 10000

    def generate_variants(
            self,
            data: dict,
            user: User,
            dataset: StudyWrapper,
            dataset_id: str
    ) -> Generator[str, None, None]:
        """Summary variants generator."""
        # Return a response instantly and make download more responsive
        yield ""
        handle_partial_permissions(self.instance_id, user, dataset_id, data)

        download_limit = None
        if not (user.is_authenticated and user.has_unlimited_download):
            download_limit = self.DOWNLOAD_LIMIT
        data.update({"limit": download_limit})

        config = dataset.config.gene_browser
        freq_col = config.frequency_column

        variants = dataset.get_gene_view_summary_variants_download(
            freq_col, **data)

        for variant in variants:
            yield variant

    @request_logging(LOGGER)
    def post(self, request: Request) -> Response:
        """Summary variants download."""
        data = expand_gene_set(parse_query_params(request.data), request.user)
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if dataset.is_remote:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = cast(StudyWrapper, dataset)

        response = FileResponse(
            self.generate_variants(data, request.user, dataset, dataset_id),
            content_type="text/tsv"
        )
        response["Content-Disposition"] = \
            "attachment; filename=summary_variants.tsv"
        response["Expires"] = "0"
        return response
