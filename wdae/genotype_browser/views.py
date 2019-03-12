'''
Created on Feb 6, 2017

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
from builtins import map
from builtins import str

from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

from datasets_api.studies_manager import get_studies_manager
from users_api.authentication import SessionAuthenticationWithoutCSRF

from helpers.logger import log_filter
from helpers.logger import LOGGER

import traceback
from rest_framework.exceptions import NotAuthenticated
import json
# from query_variants import join_line, generate_response
from datasets_api.permissions import IsDatasetAllowed
from studies.helpers import get_variants_web_preview
import logging
from gene_sets.expand_gene_set_decorator import expand_gene_set
from helpers.dae_query import join_line, generate_response

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

    def __prepare_variants_response(self, cols, rows):
        limitted_rows = []
        count = 0
        for row in rows:
            count += 1
            if count <= self.MAX_SHOWN_VARIANTS:
                limitted_rows.append(row)
            if count > self.MAX_VARIANTS:
                break

        if count <= self.MAX_VARIANTS:
            count = str(count)
        else:
            count = 'more than {}'.format(self.MAX_VARIANTS)

        return {
            'count': count,
            'cols': cols,
            'rows': limitted_rows
        }

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            dataset_id = data['datasetId']
            self.check_object_permissions(request, dataset_id)

            dataset = self.get_dataset_wdae_wrapper(dataset_id)
            # LOGGER.info("dataset " + str(dataset))
            
            response = get_variants_web_preview(
                dataset.query_variants(safe=True, **data),
                dataset.pedigree_selectors,
                data.get('pedigreeSelector', {}),
                dataset.preview_columns,
                # dataset.pedigree_columns
            )

            # pprint.pprint(response)
            response['legend'] = dataset.get_legend(safe=True, **data)

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

    @staticmethod
    def __limit(variants, limit):
        count = 0
        for variant in variants:
            if count <= limit:
                yield variant
                count += 1
            else:
                break

    @expand_gene_set
    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 download request: " +
                               str(request.data)))

        data = self._parse_query_params(request.data)
        user = request.user

        try:
            self.check_object_permissions(request, data['datasetId'])

            dataset = self.get_dataset_wdae_wrapper(data['datasetId'])

            columns = dataset.download_columns
            try:
                columns.remove('pedigree')
            except ValueError:
                pass

            # variants_data = generate_response(
            #     dataset.query_variants(safe=True, **data),
            #     columns, dataset.get_column_labels())

            variants_data = get_variants_web_preview(
                    dataset.query_variants(safe=True, **data),
                    dataset.pedigree_selectors,
                    data.get('pedigreeSelector', {}),
                    dataset.download_columns,
                    dataset.pedigree_columns
            )

            # if not (user.is_authenticated() and user.has_unlimitted_download):
            #     variants_data = self.__limit(variants_data,
            #                                  self.DOWNLOAD_LIMIT)

            response = StreamingHttpResponse(
                list(map(join_line, [variants_data['cols']] + variants_data['rows'])),
                content_type='text/tsv')

            response['Content-Disposition'] = 'attachment; filename=variants.tsv'
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
