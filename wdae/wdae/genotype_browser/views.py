from django.http.response import StreamingHttpResponse, FileResponse

from rest_framework import status
from rest_framework.response import Response

import json
import logging

from utils.logger import LOGGER
from utils.streaming_response_util import iterator_to_json
from utils.logger import request_logging

from query_base.query_base import QueryBaseView

from gene_sets.expand_gene_set_decorator import expand_gene_set

from datasets_api.permissions import \
    get_allowed_genotype_studies


logger = logging.getLogger(__name__)


def handle_partial_permissions(user, dataset_id: str, request_data: dict):
    """A user may have only partial access to a dataset based
    on which of its constituent studies he has rights to access.
    This method attaches these rights to the request as study filters
    in order to filter variants from studies the user cannot access.
    """

    request_data["allowed_studies"] = \
        get_allowed_genotype_studies(user, dataset_id)


class GenotypeBrowserConfigView(QueryBaseView):
    @request_logging(LOGGER)
    def get(self, request):
        data = request.query_params
        dataset_id = data.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        study_wrapper = self.gpf_instance.get_wdae_wrapper(dataset_id)

        # preview_info = dict(study_wrapper.get_wdae_preview_info(
        #     data, GenotypeBrowserQueryView.MAX_SHOWN_VARIANTS
        # ))

        preview_info = dict()

        config = study_wrapper.config

        preview_info.update(config.genotype_browser)

        result_config = {k: preview_info[k] for k in [
            # "legend",
            # "maxVariantsCount",
            "preview_columns",
            "download_columns",
            "summary_preview_columns",
            "summary_download_columns",
            "columns",
            "column_groups"
        ]}

        # TODO Should we merge genotype and phenotype columns before sending
        # them to the frontend? Does it care for the distinction?

        return Response(result_config, status=status.HTTP_200_OK)


class GenotypeBrowserQueryView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 variants request: " + str(request.data))

        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if "genomicScores" in data:
            scores = data["genomicScores"]
            for score in scores:
                if score["rangeStart"] is None and score["rangeEnd"] is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        if "sources" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        sources = data.pop("sources")

        is_download = data.pop("download", False)

        max_variants = data.pop(
            "maxVariantsCount", self.MAX_SHOWN_VARIANTS + 1)
        if max_variants == -1:
            # unlimitted variants preview
            max_variants = None

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        user = request.user

        handle_partial_permissions(user, dataset_id, data)

        response = dataset.query_variants_wdae(
            data, sources, max_variants_count=max_variants
        )

        if is_download:
            response = FileResponse(response, content_type="text/tsv")
        else:
            response = StreamingHttpResponse(
                iterator_to_json(response),
                status=status.HTTP_200_OK,
                content_type="text/event-stream",
            )

        response["Cache-Control"] = "no-cache"
        return response


class QueryPreviewView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 preview request: " + str(request.data))

        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        # LOGGER.info('dataset ' + str(dataset))
        # response = dataset.get_wdae_preview_info(
        #     data,
        #     max_variants_count=QueryPreviewView.MAX_SHOWN_VARIANTS,
        # )
        response = dict()

        return Response(response, status=status.HTTP_200_OK)


class QueryDownloadView(QueryBaseView):

    DOWNLOAD_LIMIT = 10000

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert "queryData" in res
        query = json.loads(res["queryData"])
        return query

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 download request: " + str(request.data))

        data = self._parse_query_params(request.data)
        user = request.user

        dataset_id = data.pop("datasetId")

        handle_partial_permissions(user, dataset_id, data)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        download_limit = None
        if not (user.is_authenticated and user.has_unlimitted_download):
            download_limit = self.DOWNLOAD_LIMIT

        variants_data = dataset.get_variants_wdae_download(
            data, max_variants_count=download_limit
        )

        response = FileResponse(variants_data, content_type="text/tsv")

        response["Content-Disposition"] = "attachment; filename=variants.tsv"
        response["Expires"] = "0"
        return response


class QuerySummaryVariantsView(QueryBaseView):
    MAX_SHOWN_VARIANTS = 1000

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        max_variants = data.pop(
            "maxVariantsCount", self.MAX_SHOWN_VARIANTS + 1)

        if max_variants == -1:
            max_variants = None

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        user = request.user

        handle_partial_permissions(user, dataset_id, data)

        response = dataset.get_summary_variants_wdae_preview(
            data, max_variants)

        response = StreamingHttpResponse(
            iterator_to_json(response),
            status=status.HTTP_200_OK,
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        return response


class QueryPreviewSummaryVariantsView(QueryBaseView):
    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 preview request: " + str(request.data))

        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        # LOGGER.info('dataset ' + str(dataset))
        try:
            response = dataset.get_summary_wdae_preview_info(
                data,
                max_variants_count=QuerySummaryVariantsView.MAX_SHOWN_VARIANTS,
            )
        except(Exception):
            return Response(
                {"error": "Summary preview columns are not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(response, status=status.HTTP_200_OK)


class QuerySummaryVariantsDownloadView(QueryBaseView):
    DOWNLOAD_LIMIT = 10000

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert "queryData" in res
        query = json.loads(res["queryData"])
        return query

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 download request: " + str(request.data))

        data = self._parse_query_params(request.data)
        user = request.user

        dataset_id = data.pop("datasetId")

        handle_partial_permissions(user, dataset_id, data)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        download_limit = None
        if not (user.is_authenticated and user.has_unlimitted_download):
            download_limit = self.DOWNLOAD_LIMIT

        try:
            variants_data = dataset.get_summary_variants_wdae_download(
                data, max_variants_count=download_limit
            )
        except(Exception):
            return Response(
                {"error": "Summary download columns are not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = FileResponse(variants_data, content_type="text/tsv")

        response["Content-Disposition"] = "attachment; filename=variants.tsv"
        response["Expires"] = "0"
        return response
