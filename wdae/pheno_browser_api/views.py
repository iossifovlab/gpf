'''
Created on Apr 21, 2017

@author: lubo
'''

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import preloaded
from pheno_browser.models import VariableBrowserModelManager


class PhenoInstrumentsView(APIView):

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_factory = self.datasets.get_factory()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.datasets_factory.get_dataset(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = dataset.pheno_db.instruments.keys()
        res = {
            'instruments': instruments,
            'default': instruments[0],
        }
        return Response(res)


class PhenoMeasuresView(APIView):
    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_factory = self.datasets.get_factory()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.datasets_factory.get_dataset(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get('instrument', None)
        if instrument is None:
            instruments = dataset.pheno_db.instruments.keys()
            instrument = instruments[0]

        browser_dbfile = dataset.pheno_db.get_browser_dbfile()
        with VariableBrowserModelManager(dbfile=browser_dbfile) as vm:
            df = vm.load_df(where="instrument_name='{}'".format(instrument))
        res = []
        for row in df.itertuples():
            res.append(dict(row._asdict()))
        return Response({
            'base_image_url': '/static/pheno_browser/',
            'measures': res,
        })
