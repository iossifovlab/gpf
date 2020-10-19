import logging
from rest_framework import status
from rest_framework.response import Response

from query_base.query_base import QueryBaseView

from utils.logger import request_logging
from utils.streaming_response_util import iterator_to_json
from gene_sets.expand_gene_set_decorator import expand_gene_set


LOGGER = logging.getLogger(__name__)


class ConfigView(QueryBaseView):
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
        config = dataset.config.gene_view

        return Response(config, status=status.HTTP_200_OK)


class QueryVariantsView(QueryBaseView):
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

        config = dataset.config.gene_view
        freq_col = config.frequency_column

        variants = dataset.get_gene_view_summary_variants(freq_col, data)

        response = Response(
            iterator_to_json(variants),
            status=status.HTTP_200_OK,
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"

        return response
