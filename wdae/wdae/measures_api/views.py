import logging
import numpy as np

from rest_framework import status
from rest_framework.response import Response

from dae.pheno.common import MeasureType

from query_base.query_base import QueryBaseView

logger = logging.getLogger(__name__)


class PhenoMeasuresView(QueryBaseView):
    def get(self, request, measure_type):
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None

        if dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        assert measure_type == "continuous" or measure_type == "categorical"

        res = dataset.phenotype_data.get_measures(measure_type=measure_type)
        if measure_type == "continuous":
            res = [
                {
                    "measure": m.measure_id,
                    "min": m.min_value,
                    "max": m.max_value,
                }
                for m in list(res.values())
            ]
        elif measure_type == "categorical":
            res = [
                {"measure": m.measure_id, "domain": m.values_domain.split(",")}
                for m in list(res.values())
            ]
        return Response(res, status=status.HTTP_200_OK)


class PhenoMeasureHistogramView(QueryBaseView):
    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        assert dataset is not None
        assert dataset.phenotype_data is not None
        assert "measure" in data

        pheno_measure = data["measure"]
        assert dataset.phenotype_data.has_measure(pheno_measure)

        measure = dataset.phenotype_data.get_measure(pheno_measure)
        assert measure.measure_type == MeasureType.continuous

        df = dataset.phenotype_data.get_measure_values_df(pheno_measure)

        m = df[pheno_measure]
        bars, bins = np.histogram(
            df[np.logical_not(np.isnan(m.values))][pheno_measure].values, 25
        )

        result = {
            "measure": pheno_measure,
            "desc": "",
            "min": min(bins),
            "max": max(bins),
            "bars": bars,
            "bins": bins,
            "step": (measure.max_value - measure.min_value) / 1000.0,
        }
        return Response(result, status=status.HTTP_200_OK)


class PhenoMeasurePartitionsView(QueryBaseView):
    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
        assert dataset.phenotype_data is not None
        assert "measure" in data
        pheno_measure = data["measure"]

        assert dataset.phenotype_data.has_measure(pheno_measure)

        df = dataset.phenotype_data.get_measure_values_df(pheno_measure)

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
        mdf = df[
            np.logical_and(df[pheno_measure] >= mmin, df[pheno_measure] < mmax)
        ]

        res = {
            "left": {"count": len(ldf), "percent": len(ldf) / total},
            "mid": {"count": len(mdf), "percent": len(mdf) / total},
            "right": {"count": len(rdf), "percent": len(rdf) / total},
        }
        return Response(res)


class PhenoMeasureRegressionsView(QueryBaseView):
    def __init__(self):
        super(PhenoMeasureRegressionsView, self).__init__()
        self.pheno_config = self.gpf_instance.get_phenotype_db_config()

    def get_browser_dbfile(self, dbname):
        browser_dbfile = self.pheno_config[dbname].browser_dbfile
        assert browser_dbfile is not None
        return browser_dbfile

    def get(self, request):
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        regressions = self.gpf_instance.get_regressions(dataset)

        if regressions is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            regressions, status=status.HTTP_200_OK
        )
