'''
Created on Apr 21, 2017

@author: lubo
'''
import numpy as np

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import preloaded
from pheno_browser.models import VariableBrowserModelManager
from django.conf import settings
import os
from pheno_browser_api.common import get_cache_dir


class PhenoInstrumentsView(APIView):

    def __init__(self):
        register = preloaded.register
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

        instruments = sorted(dataset.pheno_db.instruments.keys())
        res = {
            'instruments': instruments,
            'default': instruments[0],
        }
        return Response(res)


def isnan(val):
    return val is None or np.isnan(val)


class PhenoMeasuresView(APIView):
    def __init__(self):
        register = preloaded.register
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_factory = self.datasets.get_factory()
        self.base_url = getattr(
            settings,
            "PHENO_BROWSER_BASE_URL",
            "/static/pheno_browser/")

    def get_browser_dbfile(self, dbname):
        cache_dir = get_cache_dir(dbname)

        browser_db = "{}_browser.db".format(dbname)
        return os.path.join(
            cache_dir,
            browser_db
        )

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

        browser_dbfile = self.get_browser_dbfile(
            dataset.pheno_db.pheno_db)
        print(browser_dbfile)

        with VariableBrowserModelManager(dbfile=browser_dbfile) as vm:
            df = vm.load_df(where="instrument_name='{}'".format(instrument))
        res = []
        for row in df.itertuples():
            m = dict(vars(row))
            if isnan(m['pvalue_correlation_nviq_male']):
                m['pvalue_correlation_nviq_male'] = "NaN"
            if isnan(m['pvalue_correlation_age_male']):
                m['pvalue_correlation_age_male'] = "NaN"
            if isnan(m['pvalue_correlation_nviq_female']):
                m['pvalue_correlation_nviq_female'] = "NaN"
            if isnan(m['pvalue_correlation_age_female']):
                m['pvalue_correlation_age_female'] = "NaN"

            if m['values_domain'] is None:
                m['values_domain'] = "[0, 0]"

            res.append(m)
        return Response({
            'base_image_url': self.base_url,
            'measures': res,
        })
