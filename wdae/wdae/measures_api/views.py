import logging
from typing import cast, Any
import numpy as np

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from dae.pheno.common import MeasureType

from query_base.query_base import QueryDatasetView

logger = logging.getLogger(__name__)


class PhenoMeasuresView(QueryDatasetView):
    def get(self, request: Request, measure_type: str) -> Response:
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None

        if dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        assert measure_type == "continuous" or measure_type == "categorical"

        measures = dataset.phenotype_data.get_measures(
            measure_type=measure_type
        )
        res: list[dict[str, Any]]
        if measure_type == "continuous":
            res = [
                {
                    "measure": m.measure_id,
                    "min": m.min_value,
                    "max": m.max_value,
                }
                for m in list(measures.values())
            ]
        elif measure_type == "categorical":
            res = [
                {
                    "measure": m.measure_id,
                    "domain": cast(str, m.values_domain).split(",")
                }
                for m in list(measures.values())
            ]
        return Response(res, status=status.HTTP_200_OK)


class PhenoMeasureHistogramView(QueryDatasetView):
    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
        assert dataset.phenotype_data is not None
        if "measure" in data \
                and not dataset.phenotype_data.has_measure(data["measure"]):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        assert "measure" in data

        pheno_measure = data["measure"]
        assert dataset.phenotype_data.has_measure(pheno_measure)

        measure = dataset.phenotype_data.get_measure(pheno_measure)
        if measure.measure_type is not MeasureType.continuous:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        df = dataset.phenotype_data.get_people_measure_values_df(
            [pheno_measure]
        )

        m = df[pheno_measure]
        bars, bins = np.histogram(
            df[np.logical_not(np.isnan(m.values))][pheno_measure].values, 25
        )

        m_range = cast(
            float, measure.max_value
        ) - cast(float, measure.min_value)

        result = {
            "measure": pheno_measure,
            "desc": "",
            "min": min(bins),
            "max": max(bins),
            "bars": bars,
            "bins": bins,
            "step": (m_range) / 1000.0,
        }
        return Response(result, status=status.HTTP_200_OK)


class PhenoMeasurePartitionsView(QueryDatasetView):
    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
        assert dataset.phenotype_data is not None
        assert "measure" in data
        pheno_measure = data["measure"]

        assert dataset.phenotype_data.has_measure(pheno_measure)

        df = dataset.phenotype_data.get_people_measure_values_df(
            [pheno_measure]
        )

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


class PhenoMeasureRegressionsView(QueryDatasetView):
    def __init__(self) -> None:
        super(PhenoMeasureRegressionsView, self).__init__()
        self.pheno_config = self.gpf_instance.get_phenotype_db_config()

    def get_browser_dbfile(self, dbname) -> str:
        browser_dbfile = self.pheno_config[dbname].browser_dbfile
        assert browser_dbfile is not None
        return browser_dbfile

    def get(self, request: Request) -> Response:
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if dataset is None or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        print(dataset_id)
        print(dataset)
        print(dataset.phenotype_data)
        print(dataset.phenotype_data.get_regressions())

        regressions = dataset.phenotype_data.get_regressions()

        if regressions is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            regressions, status=status.HTTP_200_OK
        )
