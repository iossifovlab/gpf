'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response


from helpers.logger import log_filter, LOGGER
from datasets.config import DatasetsConfig
import traceback
from datasets.dataset import DatasetsFactory


class QueryPreviewView(views.APIView):

    def __init__(self):
        self.datasets_config = DatasetsConfig()
        self.datasets = DatasetsFactory(self.datasets_config)

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
            dataset_id = data['datasetId']
            dataset = self.datasets.get_dataset(dataset_id)

            legend = self.prepare_legend_response(dataset)
            variants = dataset.get_variants_preview(
                safe=True,
                **data)
            res = self.prepare_variants_resonse(variants)

            res['legend'] = legend

            return Response(res, status=status.HTTP_200_OK)
        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
