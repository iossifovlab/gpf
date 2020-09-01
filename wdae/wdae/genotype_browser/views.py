from django.http.response import StreamingHttpResponse, FileResponse
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response

import json
import logging

from utils.logger import LOGGER
from utils.streaming_response_util import iterator_to_json
from utils.logger import request_logging

from query_base.query_base import QueryBaseView

from gene_sets.expand_gene_set_decorator import expand_gene_set

from datasets_api.models import Dataset


logger = logging.getLogger(__name__)


def handle_partial_permissions(user, dataset_id: str, request_data: dict):
    """A user may have only partial access to a dataset based
    on which of its constituent studies he has rights to access.
    This method attaches these rights to the request as study filters
    in order to filter variants from studies the user cannot access.
    """

    any_dataset = user.groups.filter(Q(name="admin") | Q(name="any_dataset"))
    logger.debug(f"any_dataset: {any_dataset} ({bool(any_dataset)})")
    any_dataset = bool(any_dataset)

    user_allowed_datasets = {
        dataset_object.dataset_id
        for dataset_object in Dataset.objects.all()
        if any_dataset or user.groups.filter(name=dataset_object.dataset_id).exists()
    }
    logger.debug(f"user allowed datasets: {user_allowed_datasets}")

    if dataset_id not in user_allowed_datasets:
        if request_data.get("study_filters"):
            combined_filters = \
                set(request_data["study_filters"]) \
                & user_allowed_datasets
        else:
            combined_filters = user_allowed_datasets
        request_data["study_filters"] = list(combined_filters)


class QueryPreviewView(QueryBaseView):
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
        response = dataset.get_wdae_preview_info(
            data,
            max_variants_count=QueryPreviewVariantsView.MAX_SHOWN_VARIANTS,
        )

        # pprint.pprint(response)

        return Response(response, status=status.HTTP_200_OK)


class QueryPreviewVariantsView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 10000

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 preview request: " + str(request.data))

        data = request.data
        dataset_id = data.pop("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        user = request.user

        handle_partial_permissions(user, dataset_id, data)

        # LOGGER.info('dataset ' + str(dataset))
        response = dataset.get_variants_wdae_preview(
            data, max_variants_count=self.MAX_SHOWN_VARIANTS
        )

        # pprint.pprint(response)

        response = StreamingHttpResponse(
            iterator_to_json(response),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response


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
