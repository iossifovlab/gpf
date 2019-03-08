'''
Created on Apr 21, 2017

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
import os
import numpy as np

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from datasets_api.studies_manager import get_studies_manager
from pheno_browser_api.common import PhenoBrowserCommon
from users_api.authentication import SessionAuthenticationWithoutCSRF
from datasets_api.permissions import IsDatasetAllowed
from django.http.response import HttpResponse
from pheno_browser.db import DbManager


class PhenoInstrumentsView(APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.datasets_facade = get_studies_manager().get_dataset_facade()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.datasets_facade.get_dataset(dataset_id)
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
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.datasets_facade = get_studies_manager().get_dataset_facade()

        self.base_url = getattr(
            settings,
            "PHENO_BROWSER_BASE_URL",
            "/static/pheno_browser/")

    def get_browser_dbfile(self, dbname):
        cache_dir = PhenoBrowserCommon.get_cache_dir(dbname)

        browser_db = "{}_browser.db".format(dbname)
        return os.path.join(
            cache_dir,
            browser_db
        )

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.datasets_facade.get_dataset(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get('instrument', None)
        if instrument is None:
            instruments = list(dataset.pheno_db.instruments.keys())
            instrument = instruments[0]

        browser_dbfile = self.get_browser_dbfile(
            dataset.pheno_name)

        db = DbManager(dbfile=browser_dbfile)
        db.build()

        df = db.get_instrument_df(instrument)

        res = []
        for row in df.to_dict('records'):
            print((row, type(row)))
            m = row
            print(m)
            if isnan(m['pvalue_correlation_nviq_male']):
                m['pvalue_correlation_nviq_male'] = "NaN"
            if isnan(m['pvalue_correlation_age_male']):
                m['pvalue_correlation_age_male'] = "NaN"
            if isnan(m['pvalue_correlation_nviq_female']):
                m['pvalue_correlation_nviq_female'] = "NaN"
            if isnan(m['pvalue_correlation_age_female']):
                m['pvalue_correlation_age_female'] = "NaN"

            if m['values_domain'] is None:
                m['values_domain'] = ""
            m['measure_type'] = m['measure_type'].name
            res.append(m)
        return Response({
            'base_image_url': self.base_url,
            'measures': res,
        })


class PhenoMeasuresDownload(APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.datasets_facade = get_studies_manager().get_dataset_facade()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.datasets_facade.get_dataset(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get('instrument', None)
        if instrument is None:
            instruments = list(dataset.pheno_db.instruments.keys())
            instrument = instruments[0]

        df = dataset.pheno_db.get_instrument_values_df(instrument)
        df_csv = df.to_csv(index=False, encoding="utf-8")

        response = HttpResponse(df_csv, content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=instrument.csv'
        response['Expires'] = '0'
        return response
