'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

from users_api.authentication import SessionAuthenticationWithoutCSRF

from helpers.logger import log_filter, LOGGER
import traceback
import preloaded
from rest_framework.exceptions import NotAuthenticated
import json
from query_variants import join_line
import itertools
from datasets_api.permissions import IsDatasetAllowed


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

    def __init__(self):
        super(QueryPreviewView, self).__init__()

    def prepare_variants_response(self, columns, all_variants):
        common_cols = list(set.intersection(*[set(l) for l in columns]))
        cols_map = {name: index for (index, name) in enumerate(common_cols)}

        rows = []
        count = 0

        for current_cols, variants in zip(columns, all_variants):
            for v in variants:
                count += 1
                if count <= 1000:
                    row = [None for x in range(len(common_cols))]
                    for i, col_name in enumerate(current_cols):
                        if col_name in cols_map:
                            index = cols_map[col_name]
                            row[index] = v[i]
                    rows.append(row)
                if count > 2000:
                    break
            if count > 2000:
                break

        if count <= 2000:
            count = str(count)
        else:
            count = 'more than 2000'

        return {
            'count': count,
            'cols': common_cols,
            'rows': rows
        }

    def prepare_legend_response(self, dataset, **data):
        legend = dataset.get_pedigree_selector(**data)
        response = legend.domain[:]
        response.append(legend.default)
        return response

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            legend = []
            dataset_id = data['datasetId']
            all_variants = []
            columns = []
            for dataset_id in data['datasetId']:
                dataset = self.datasets_factory.get_dataset(dataset_id)
                self.check_object_permissions(request, dataset_id)

                for leg in self.prepare_legend_response(dataset, **data):
                    if leg not in legend:
                        legend.append(leg)

                v = dataset.get_variants_preview(
                    safe=True,
                    limit=2000,
                    **data
                )
                columns.append(v.next())
                all_variants.append(v)
            res = self.prepare_variants_response(columns, all_variants)

            res['legend'] = legend

            return Response(res, status=status.HTTP_200_OK)
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
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
            self.check_object_permissions(request, dataset_id)

            generator = dataset.get_variants_csv(safe=True, **data)

            response = StreamingHttpResponse(
                itertools.chain(
                    itertools.imap(join_line, generator)),
                content_type='text/csv')

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
