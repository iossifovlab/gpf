'''
Created on Feb 6, 2017

@author: lubo
'''
import itertools

from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

from users_api.authentication import SessionAuthenticationWithoutCSRF

from helpers.logger import log_filter, LOGGER
import traceback
import preloaded
from rest_framework.exceptions import NotAuthenticated
import json
from query_variants import join_line, generate_web_response
from datasets_api.permissions import IsDatasetAllowed
from functools import partial
from datasets.metadataset import MetaDataset


class QueryBaseView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        register = preloaded.register
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()


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

        if count <= self.MAX_SHOWN_VARIANTS:
            count = str(count)
        else:
            count = 'more than {}'.format(self.MAX_VARIANTS)

        return {
            'count': count,
            'cols': cols,
            'rows': limitted_rows
        }

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            dataset_id = data['datasetId']
            self.check_object_permissions(request, dataset_id)

            if dataset_id == MetaDataset.ID:
                data['dataset_ids'] = filter(
                    lambda dataset_id: IsDatasetAllowed.user_has_permission(
                        request.user, dataset_id),
                    self.datasets_config.get_dataset_ids())

            dataset = self.datasets_factory.get_dataset(dataset_id)

            response = self.__prepare_variants_response(
                **generate_web_response(
                    dataset.get_variants(safe=True, **data),
                    dataset.get_columns()))

            response['legend'] = dataset.get_legend(safe=True, **data)

            return Response(response, status=status.HTTP_200_OK)
        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class QueryDownloadView(QueryBaseView):

    def __init__(self):
        super(QueryDownloadView, self).__init__()

    def _parse_query_params(self, data):
        print(data)

        res = {str(k): str(v) for k, v in data.items()}
        assert 'queryData' in res
        query = json.loads(res['queryData'])
        return query

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 download request: " +
                               str(request.data)))

        data = self._parse_query_params(request.data)

        try:
            self.check_object_permissions(request, data['datasetId'])

            if data['datasetId'] == MetaDataset.ID:
                data['dataset_ids'] = filter(
                    lambda dataset_id: IsDatasetAllowed.user_has_permission(
                        request.user, dataset_id),
                    self.datasets_config.get_dataset_ids())

            dataset = self.datasets_factory.get_dataset(data['datasetId'])

            columns = dataset.get_columns()
            columns.remove('_pedigree_')
            variants_data = generate_web_response(
                dataset.get_variants(safe=True, user=request.user, **data),
                columns)

            all_gens = itertools.imap(join_line,
                itertools.chain([variants_data['cols']], variants_data['rows']))

            response = StreamingHttpResponse(
                all_gens, content_type='text/csv'
            )

            response['Content-Disposition'] = 'attachment; filename=unruly.csv'
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

        return response
