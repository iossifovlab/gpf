'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response


from helpers.logger import log_filter, LOGGER
from datasets.config import DatasetsConfig
from genotype_query.query import QueryDataset


class QueryPreviewView(views.APIView):

    def __init__(self):
        self.datasets = DatasetsConfig()
        self.query = QueryDataset(self.datasets.get_datasets())

    def prepare_variants_resonse(self, variants):
        rows = []
        cols = variants.next()
        count = 0
        for v in variants:
            count += 1
            if count <= 1000:
                rows.append(v)
            if count > 2000:
                break
        if count <= 2000:
            count = str(count)
        else:
            count = 'more than 2000'

        return {
            'count': count,
            'cols': cols,
            'rows': rows
        }

    def prepare_legend_response(self, data):
        dataset = self.query.get_dataset(**data)
        legend = self.query.get_legend(dataset, **data)
        response = legend.domain[:]
        response.append(legend.default)
        return response

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            res = {}
            res['legend'] = self.prepare_legend_response(data)

            variants = self.query.get_variants_preview(safe=True, **data)
            res.update(variants)

            return Response(status=status.HTTP_200_OK)
        except Exception:
            return Response(res, status.HTTP_400_BAD_REQUEST)
