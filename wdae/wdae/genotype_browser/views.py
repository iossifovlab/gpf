from django.http.response import StreamingHttpResponse, FileResponse
from rest_framework import status
from rest_framework.response import Response

import json
import logging

from utils.logger import log_filter
from utils.logger import LOGGER
from utils.streaming_response_util import iterator_to_json

from query_base.query_base import QueryBaseView

from gene_sets.expand_gene_set_decorator import expand_gene_set


logger = logging.getLogger(__name__)


class QueryPreviewView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    MAX_VARIANTS = 2000

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, 'query v3 preview request: ' +
                               str(request.data)))

        data = request.data
        dataset_id = data.pop('datasetId', None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)

        # LOGGER.info('dataset ' + str(dataset))
        response = dataset.get_wdae_preview_info(data)

        # pprint.pprint(response)

        return Response(response, status=status.HTTP_200_OK)


class QueryPreviewVariantsView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, 'query v3 preview request: ' +
                               str(request.data)))

        data = request.data
        dataset_id = data.pop('datasetId', None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)

        # LOGGER.info('dataset ' + str(dataset))
        response = dataset.get_variants_wdae_preview(
            data,
            max_variants_count=self.MAX_SHOWN_VARIANTS
        )

        # pprint.pprint(response)

        return StreamingHttpResponse(
            iterator_to_json(response),
            status=status.HTTP_200_OK,
            content_type='text/event-stream'
        )


class QueryDownloadView(QueryBaseView):

    DOWNLOAD_LIMIT = 10000

    def _parse_query_params(self, data):
        print(data)

        res = {str(k): str(v) for k, v in list(data.items())}
        assert 'queryData' in res
        query = json.loads(res['queryData'])
        return query

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, 'query v3 download request: ' +
                               str(request.data)))

        data = self._parse_query_params(request.data)
        user = request.user

        dataset_id = data.pop('datasetId')

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)

        download_limit = None
        if not (user.is_authenticated and user.has_unlimitted_download):
            download_limit = self.DOWNLOAD_LIMIT

        variants_data = dataset.get_variants_wdae_download(
            data,
            max_variants_count=download_limit
        )

        response = FileResponse(variants_data, content_type='text/tsv')

        response['Content-Disposition'] = \
            'attachment; filename=variants.tsv'
        response['Expires'] = '0'
        return response
