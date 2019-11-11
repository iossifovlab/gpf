from django.http.response import StreamingHttpResponse
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated

import json
import logging
import traceback

from utils.logger import log_filter
from utils.logger import LOGGER

from gpf_instance.gpf_instance import get_gpf_instance

from datasets_api.permissions import IsDatasetAllowed
from users_api.authentication import SessionAuthenticationWithoutCSRF

from gene_sets.expand_gene_set_decorator import expand_gene_set


logger = logging.getLogger(__name__)


class QueryBaseView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.variants_db = get_gpf_instance().variants_db


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

            dataset = self.variants_db.get_wdae_wrapper(dataset_id)

            # LOGGER.info("dataset " + str(dataset))
            response = dataset.get_variants_wdae_preview(
                data,
                max_variants_count=self.MAX_SHOWN_VARIANTS,
                variants_hard_max=self.MAX_VARIANTS
            )

            # pprint.pprint(response)

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

            dataset = self.variants_db.get_wdae_wrapper(dataset_id)

            download_limit = None
            if not (user.is_authenticated and user.has_unlimitted_download):
                download_limit = self.DOWNLOAD_LIMIT

            variants_data = dataset.get_variants_wdae_download(
                data,
                max_variants_count=download_limit,
                variants_hard_max=self.DOWNLOAD_LIMIT
            )

            response = \
                StreamingHttpResponse(variants_data, content_type='text/tsv')

            response['Content-Disposition'] = \
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
