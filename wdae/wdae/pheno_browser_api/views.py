import os
import numpy as np

from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.http.response import HttpResponse

from dae.pheno_browser.db import DbManager

from query_base.query_base import QueryBaseView


class PhenoBrowserBaseView(QueryBaseView):

    def __init__(self):
        super(PhenoBrowserBaseView, self).__init__()

        self.pheno_config = self.variants_db.pheno_factory.config

    def get_cache_dir(self, dbname):

        cache_dir = getattr(
            settings,
            "PHENO_BROWSER_CACHE",
            None)
        dbdir = os.path.join(cache_dir, dbname)
        return dbdir

    def get_browser_dbfile(self, dbname):
        browser_dbfile = self.pheno_config[dbname].browser_dbfile
        assert browser_dbfile is not None
        assert os.path.exists(browser_dbfile)
        return browser_dbfile

    def get_browser_images_dir(self, dbname):
        browser_images_dir = self.pheno_config[dbname].browser_images_dir
        assert browser_images_dir is not None
        assert os.path.exists(browser_images_dir)
        assert os.path.isdir(browser_images_dir)
        return browser_images_dir

    def get_browser_images_url(self, dbname):
        browser_images_url = self.pheno_config[dbname].browser_images_url
        assert browser_images_url is not None
        return browser_images_url


class PhenoInstrumentsView(PhenoBrowserBaseView):

    def __init__(self):
        super(PhenoInstrumentsView, self).__init__()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)
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


class PhenoMeasuresView(PhenoBrowserBaseView):

    def __init__(self):
        super(PhenoMeasuresView, self).__init__()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get('instrument', None)
        search_term = request.query_params.get('search', None)

        if instrument and instrument not in dataset.pheno_db.instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        browser_dbfile = self.get_browser_dbfile(dataset.config.phenoDB)
        browser_images_url = self.get_browser_images_url(
            dataset.config.phenoDB)

        db = DbManager(dbfile=browser_dbfile)
        db.build()

        df = db.search_measures(instrument, search_term)

        res = []
        for m in df.to_dict('records'):

            if m['values_domain'] is None:
                m['values_domain'] = ""
            m['measure_type'] = m['measure_type'].name

            m['regressions'] = db.get_regression_values(m['measure_id']) or []

            for reg in m['regressions']:
                reg = dict(reg)
                if isnan(reg['pvalue_regression_male']):
                    reg['pvalue_regression_male'] = "NaN"
                if isnan(reg['pvalue_regression_female']):
                    reg['pvalue_regression_female'] = "NaN"

            res.append(m)

        return Response({
            'base_image_url': browser_images_url,
            'measures': res,
            'has_descriptions': db.has_descriptions,
            'regression_names': db.regression_display_names
        })


class PhenoMeasuresDownload(PhenoBrowserBaseView):

    def __init__(self):
        super(PhenoMeasuresDownload, self).__init__()

    def get(self, request):
        if 'dataset_id' not in request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']

        dataset = self.variants_db.get_wdae_wrapper(dataset_id)
        if dataset is None or dataset.pheno_db is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = request.query_params.get('instrument', None)
        if not instrument:
            measure_ids = list(dataset.pheno_db.measures.keys())
            df = dataset.pheno_db.get_values_df(measure_ids)
        else:
            if instrument not in dataset.pheno_db.instruments:
                return Response(status=status.HTTP_404_NOT_FOUND)
            df = dataset.pheno_db.get_instrument_values_df(instrument)

        df_csv = df.to_csv(index=False, encoding="utf-8")

        response = HttpResponse(df_csv, content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=instrument.csv'
        response['Expires'] = '0'
        return response
