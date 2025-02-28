import logging
import operator
from typing import Any, cast

import numpy as np
import pandas as pd
from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.pheno.common import MeasureType

logger = logging.getLogger(__name__)


class PhenoMeasuresView(QueryBaseView):
    """View for phenotype measures."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request, measure_type: str) -> Response:
        """Get phenotype measures."""
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None

        if not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        assert measure_type in {"continuous", "categorical"}

        measures = dataset.phenotype_data.get_measures(
            measure_type=MeasureType.from_str(measure_type),
        )
        res: list[dict[str, Any]] = []
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
                    "domain": cast(str, m.values_domain).split(","),
                }
                for m in list(measures.values())
            ]
        return Response(res, status=status.HTTP_200_OK)


class PhenoMeasureListView(QueryBaseView):
    """View for phenotype measures ids."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get phenotype measures ids."""
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None

        if not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        res: list[dict[str, Any]] = []

        continuous_measures = dataset.phenotype_data.get_measures(
            measure_type=MeasureType.from_str("continuous"),
        )
        res = [
            {
                "measure": m.measure_id,
                "description": m.description,
            }
            for m in list(continuous_measures.values())
        ]

        categorical_measures = dataset.phenotype_data.get_measures(
            measure_type=MeasureType.from_str("categorical"),
        )
        res += [
            {
                "measure": m.measure_id,
                "description": m.description,
            }
            for m in list(categorical_measures.values())
        ]

        res = sorted(res, key=operator.itemgetter("measure"))

        return Response(res, status=status.HTTP_200_OK)


class PhenoMeasureHistogramView(QueryBaseView):
    """View for phenotype measure histograms."""

    def post(self, request: Request) -> Response:
        """Get phenotype measure histograms."""
        data = request.data
        assert isinstance(data, dict)
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
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
            [pheno_measure],
        )

        m = df[pheno_measure]
        bars, bins = np.histogram(
            df[np.logical_not(np.isnan(m.values))][pheno_measure].values, 25,
        )

        m_range = cast(
            float, measure.max_value,
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


class PhenoMeasureHistogramViewBeta(QueryBaseView):
    """View for phenotype measure histograms."""

    def post(self, request: Request) -> Response:
        """Get phenotype measure histograms."""
        data = request.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        assert isinstance(data, dict)

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
        if "measure" in data \
                and not dataset.phenotype_data.has_measure(data["measure"]):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        assert "measure" in data

        pheno_measure = data["measure"]
        assert pheno_measure is not None
        assert dataset.phenotype_data.has_measure(pheno_measure)

        measure = dataset.phenotype_data.get_measure(pheno_measure)
        df = dataset.phenotype_data.get_people_measure_values_df(
            [pheno_measure],
        )
        m = df[pheno_measure]
        df = df[np.logical_not(pd.isna(m.values))]

        result = {
            "measure": measure.measure_id,
            "histogram": None,
        }
        if measure.histogram_type is NumberHistogram:
            bars, bins = np.histogram(
                df[pheno_measure].values,
                25,
            )
            number_hist_conf = NumberHistogramConfig(
                (np.min(bins).item(), np.max(bins).item()),
                25,
            )
            result["histogram"] = NumberHistogram.from_dict({
                "config": number_hist_conf.to_dict(),
                "bins": bins,
                "bars": bars,
                "min_value": np.min(bins).item(),
                "max_value": np.max(bins).item(),
            }).to_dict()
        elif measure.histogram_type is CategoricalHistogram:
            counts = {}
            for value in measure.domain:
                counts[value] = len(df[df[pheno_measure] == value])
            categorical_hist_conf = CategoricalHistogramConfig()
            result["histogram"] = CategoricalHistogram(
                categorical_hist_conf,
                counts,
            ).to_dict()
        return Response(result, status=status.HTTP_200_OK)


class PhenoMeasurePartitionsView(QueryBaseView, DatasetAccessRightsView):
    """View for phenotype measure partitions.
    Histograms can calculate gene count when min and max are not inside bins.
    Using a range that has min/max somewhere inside a bin needs a more
    accurate calculation of genes.
    """

    def post(self, request: Request) -> Response:
        """Get phenotype measure partitions."""
        data = request.data
        assert isinstance(data, dict)

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        assert dataset is not None
        assert "measure" in data
        pheno_measure = data["measure"]

        assert dataset.phenotype_data.has_measure(pheno_measure)

        df = dataset.phenotype_data.get_people_measure_values_df(
            [pheno_measure],
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


class PhenoMeasureRegressionsView(QueryBaseView):
    """View for phenotype measure regressions."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get phenotype measure regressions."""
        data = request.query_params

        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if dataset is None or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        regressions = dataset.phenotype_data.get_regressions()

        if regressions is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            regressions, status=status.HTTP_200_OK,
        )
