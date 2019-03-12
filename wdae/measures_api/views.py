'''
Created on Mar 30, 2017

@author: lubo
'''
from __future__ import division
from __future__ import unicode_literals
from past.utils import old_div
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated
import traceback
from genotype_browser.views import QueryBaseView
import numpy as np
from pheno.common import MeasureType
import logging

logger = logging.getLogger(__name__)



class PhenoMeasuresView(QueryBaseView):

    def get(self, request, measure_type):
        data = request.query_params

        try:
            dataset_id = data['datasetId']
            dataset = self.dataset_facade.get_dataset_wdae_wrapper(dataset_id)
            assert dataset is not None

            if dataset.pheno_db is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            assert measure_type == 'continuous' or \
                measure_type == 'categorical'

            res = dataset.pheno_db.get_measures(measure_type=measure_type)
            if measure_type == 'continuous':
                res = [
                    {
                        'measure': m.measure_id,
                        'min': m.min_value,
                        'max': m.max_value,
                    }
                    for m in list(res.values())
                ]
            elif measure_type == 'categorical':
                res = [
                    {
                        'measure': m.measure_id,
                        'domain': m.values_domain.split(',')
                    }
                    for m in list(res.values())
                ]
            return Response(res, status=status.HTTP_200_OK)
        except NotAuthenticated:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            logger.exception("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoMeasureHistogramView(QueryBaseView):

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.dataset_facade.get_dataset_wdae_wrapper(dataset_id)

            assert dataset is not None
            assert dataset.pheno_db is not None
            assert "measure" in data

            pheno_measure = data['measure']
            assert dataset.pheno_db.has_measure(pheno_measure)

            measure = dataset.pheno_db.get_measure(pheno_measure)
            assert measure.measure_type == MeasureType.continuous

            df = dataset.pheno_db.get_measure_values_df(
                pheno_measure)

            m = df[pheno_measure]
            bars, bins = np.histogram(
                df[np.logical_not(np.isnan(m.values))][pheno_measure].values,
                25)

            result = {
                "measure": pheno_measure,
                "desc": "",
                "min": min(bins),
                "max": max(bins),
                "bars": bars,
                "bins": bins,
                "step": old_div((measure.max_value - measure.min_value), 1000.0),
            }
            return Response(result, status=status.HTTP_200_OK)

        except NotAuthenticated:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoMeasurePartitionsView(QueryBaseView):

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.dataset_facade.get_dataset_wdae_wrapper(dataset_id)
            assert dataset is not None
            assert dataset.pheno_db is not None
            assert "measure" in data
            pheno_measure = data['measure']

            assert dataset.pheno_db.has_measure(pheno_measure)

            df = dataset.pheno_db.get_measure_values_df(pheno_measure)

            try:
                mmin = float(data["min"])
            except TypeError:
                mmin = float("-inf")

            try:
                mmax = float(data["max"])
            except TypeError:
                mmax = float("inf")

            total = 1.0 * len(df)

            ldf = df[df[pheno_measure] < mmin]
            rdf = df[df[pheno_measure] >= mmax]
            mdf = df[np.logical_and(df[pheno_measure] >= mmin,
                                    df[pheno_measure] < mmax)]

            res = {"left": {"count": len(ldf), "percent": old_div(len(ldf), total)},
                   "mid": {"count": len(mdf), "percent": old_div(len(mdf), total)},
                   "right": {"count": len(rdf), "percent": old_div(len(rdf), total)}}
            return Response(res)

        except NotAuthenticated:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            logger.exception("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
