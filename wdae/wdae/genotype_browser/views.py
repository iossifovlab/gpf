'''
Created on Feb 6, 2017

@author: lubo
'''
from django.http.response import StreamingHttpResponse
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated

import json
import logging
import traceback
import itertools

from dae.studies.helpers import get_variants_web_preview, get_variants_web_download

from helpers.logger import log_filter
from helpers.logger import LOGGER
from helpers.dae_query import join_line, columns_to_labels

from datasets_api.studies_manager import get_studies_manager
from datasets_api.permissions import IsDatasetAllowed
from users_api.authentication import SessionAuthenticationWithoutCSRF

from gene_sets.expand_gene_set_decorator import expand_gene_set


logger = logging.getLogger(__name__)


class QueryBaseView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    datasets_cache = {}

    def get_dataset_wdae_wrapper(self, dataset_id):
        if dataset_id not in self.datasets_cache:
            self.datasets_cache[dataset_id] =\
                self.variants_db.get_wdae_wrapper(dataset_id)

        return self.datasets_cache[dataset_id]

    def __init__(self):
        self.variants_db = get_studies_manager().get_variants_db()


class QueryPreviewView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    MAX_VARIANTS = 2000

    def __init__(self):
        super(QueryPreviewView, self).__init__()

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            dataset_id = data.pop('datasetId')
            self.check_object_permissions(request, dataset_id)

            dataset = self.get_dataset_wdae_wrapper(dataset_id)

            # LOGGER.info("dataset " + str(dataset))
            response = get_variants_web_preview(
                dataset, data,
                max_variants_count=self.MAX_SHOWN_VARIANTS,
                variants_hard_max=self.MAX_VARIANTS)

            # pprint.pprint(response)
            response['legend'] = dataset.get_legend(**data)

            return Response(response, status=status.HTTP_200_OK)
        except NotAuthenticated:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            logger.exception("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class QueryDownloadView(QueryBaseView):

    def __init__(self):
        super(QueryDownloadView, self).__init__()

    def _parse_query_params(self, data):
        print(data)

        res = {str(k): str(v) for k, v in list(data.items())}
        assert 'queryData' in res
        query = json.loads(res['queryData'])
        return query

    DOWNLOAD_LIMIT = 10000

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 download request: " +
                               str(request.data)))

        data = self._parse_query_params(request.data)
        user = request.user

        try:
            dataset_id = data.pop('datasetId')

            self.check_object_permissions(request, dataset_id)

            dataset = self.get_dataset_wdae_wrapper(dataset_id)

            columns = dataset.download_columns
            try:
                columns.remove('pedigree')
            except ValueError:
                pass

            download_limit = None
            if not (user.is_authenticated and user.has_unlimitted_download):
                download_limit = self.DOWNLOAD_LIMIT

            variants_data = get_variants_web_download(
                dataset, data,
                max_variants_count=download_limit,
                variants_hard_max=self.DOWNLOAD_LIMIT
            )

            columns = columns_to_labels(
                variants_data['cols'], dataset.get_column_labels())
            rows = variants_data['rows']

            response = StreamingHttpResponse(
                map(join_line, itertools.chain([columns], rows)),
                content_type='text/tsv')

            response['Content-Disposition'] =\
                'attachment; filename=variants.tsv'
            response['Expires'] = '0'
            return response
        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
