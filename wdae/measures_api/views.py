'''
Created on Mar 30, 2017

@author: lubo
'''
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated
import traceback
from genotype_browser.views import QueryBaseView
import numpy as np


class PhenoMeasuresView(QueryBaseView):

    def get(self, request, measure_type):
        data = request.query_params

        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
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
                    for m in res.values()
                ]
            elif measure_type == 'categorical':
                res = [
                    {
                        'measure': m.measure_id,
                        'domain': m.value_domain.split(',')
                    }
                    for m in res.values()
                ]
            return Response(res, status=status.HTTP_200_OK)
        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoMeasureHistogramView(QueryBaseView):

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)

            assert dataset is not None
            assert dataset.pheno_db is not None
            assert "measure" in data

            pheno_measure = data['measure']
            assert dataset.pheno_db.has_measure(pheno_measure)

            measure = dataset.pheno_db.get_measure(pheno_measure)
            assert measure.measure_type == 'continuous'

            df = dataset.pheno_db.get_measure_values_df(pheno_measure)
            m = df[pheno_measure]
            bars, bins = np.histogram(
                df[np.logical_not(np.isnan(m.values))][pheno_measure].values,
                25)

            result = {
                "measure": pheno_measure,
                "desc": "",
                "min": measure.min_value,
                "max": measure.max_value,
                "bars": bars,
                "bins": bins,
                "step": (measure.max_value - measure.min_value) / 1000.0,
            }
            return Response(result, status=status.HTTP_200_OK)

        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoMeasurePartitionsView(QueryBaseView):

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
            assert dataset is not None
            assert dataset.pheno_db is not None
            assert "measure" in data
            pheno_measure = data['measure']

            assert dataset.pheno_db.has_measure(pheno_measure)

            df = dataset.pheno_db.get_measure_values_df(pheno_measure)
            mmin = float(data["min"])
            mmax = float(data["max"])

            total = 1.0 * len(df)

            ldf = df[df[pheno_measure] < mmin]
            rdf = df[df[pheno_measure] > mmax]
            mdf = df[np.logical_and(df[pheno_measure] >= mmin,
                                    df[pheno_measure] <= mmax)]

            res = {"measure": pheno_measure,
                   "min": mmin,
                   "max": mmax,
                   "left": {"count": len(ldf), "percent": len(ldf) / total},
                   "mid": {"count": len(mdf), "percent": len(mdf) / total},
                   "right": {"count": len(rdf), "percent": len(rdf) / total}}
            return Response(res)

        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
