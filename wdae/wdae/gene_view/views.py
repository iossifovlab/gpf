import logging
from rest_framework import status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse, FileResponse

from query_base.query_base import QueryDatasetView

from utils.logger import request_logging
from utils.streaming_response_util import iterator_to_json
from gene_sets.expand_gene_set_decorator import expand_gene_set

from datasets_api.permissions import \
    handle_partial_permissions


LOGGER = logging.getLogger(__name__)


class ConfigView(QueryDatasetView):
    @expand_gene_set
    @request_logging(LOGGER)
    def get(self, request):
        data = request.query_params
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
    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user = request.user
        handle_partial_permissions(user, dataset_id, data)

        config = dataset.config.gene_browser
        freq_col = config.frequency_column

        variants = dataset.get_gene_view_summary_variants(freq_col, **data)

        response = StreamingHttpResponse(
            iterator_to_json(variants),
            status=status.HTTP_200_OK,
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"

        return response


class DownloadSummaryVariantsView(QueryDatasetView):
    DOWNLOAD_LIMIT = 10000

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user = request.user
        user = request.user
        handle_partial_permissions(user, dataset_id, data)

        download_limit = None
        if not (user.is_authenticated and user.has_unlimited_download):
            download_limit = self.DOWNLOAD_LIMIT
        data.update({"limit": download_limit})

        config = dataset.config.gene_browser
        freq_col = config.frequency_column

        variants = dataset.get_gene_view_summary_variants_download(
            freq_col, **data)
        response = FileResponse(variants, content_type="text/tsv")
        response["Content-Disposition"] = \
            "attachment; filename=summary_variants.tsv"
        response["Expires"] = "0"
        return response
