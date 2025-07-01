import logging
import math
from collections.abc import Generator
from io import StringIO
from typing import Any, cast

from dae.effect_annotation.effect import EffectTypesMixin
from dae.pheno.common import MeasureType
from dae.pheno.pheno_data import Measure
from dae.pheno_tool.tool import PhenoResult
from datasets_api.permissions import (
    get_permissions_etag,
    user_has_permission,
)
from django.http.response import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import DatasetAccessRightsView, QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from utils.expand_gene_set import expand_gene_set
from utils.query_params import parse_query_params

from pheno_tool_api.adapter import PhenoToolAdapter

logger = logging.getLogger(__name__)


class PhenoToolView(QueryBaseView):
    """View for returning pheno tool results."""

    @staticmethod
    def get_result_by_sex(
        result: dict[str, PhenoResult],
        sex: str,
    ) -> dict[str, Any]:
        return {
            "negative": {
                "count": result[sex].negative_count,
                "deviation": result[sex].negative_deviation,
                "mean": result[sex].negative_mean,
            },
            "positive": {
                "count": result[sex].positive_count,
                "deviation": result[sex].positive_deviation,
                "mean": result[sex].positive_mean,
            },
            "pValue": result[sex].pvalue,
        }

    @staticmethod
    def _build_report_description(
        measure_id: str,
        normalize_by: list[str | Any],
    ) -> str:
        if not normalize_by:
            return measure_id
        normalize_desc = " + ".join(normalize_by)
        return f"{measure_id} ~ {normalize_desc}"

    def post(self, request: Request) -> Response | StreamingHttpResponse:
        """Return pheno tool results based on POST request."""
        data = expand_gene_set(request.data)  # pyright: ignore
        study_wrapper = self.gpf_instance.get_wdae_wrapper(data["datasetId"])
        if study_wrapper is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if study_wrapper.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        adapter = cast(
            PhenoToolAdapter,
            self.gpf_instance.get_pheno_tool_adapter(study_wrapper),
        )
        data["phenoFilterFamilyIds"] = None
        if data.get("familyFilters") is not None:
            data["phenoFilterFamilyIds"] = list(
                self.query_transformer  # noqa: SLF001
                ._transform_filters_to_ids(
                    data["familyFilters"],
                    study_wrapper,
                ),
            )
        if data.get("familyPhenoFilters") is not None:
            data["phenoFilterFamilyIds"] = list(
                self.query_transformer  # noqa: SLF001
                ._transform_pheno_filters_to_ids(
                    data["familyPhenoFilters"],
                    study_wrapper,
                ),
            )

        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            result = adapter.calc_variants(data)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(result)


class PhenoToolDownload(PhenoToolView, DatasetAccessRightsView):
    """Pheno tool download view."""

    def generate_columns(
            self,
            query_data: dict[str, Any],
            adapter: PhenoToolAdapter,
    ) -> Generator[str, None, None]:
        """Pheno tool download generator function."""
        # Return a response instantly and make download more responsive
        yield ""
        result_df = adapter.produce_download_df(query_data)

        columns = [
            col
            for col in result_df.columns.tolist()
            if col not in {"normalized", "role"}
        ]

        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False, columns=columns)
        csv_buffer.seek(0)

        yield from csv_buffer.readlines()

    def post(self, request: Request) -> Response | StreamingHttpResponse:
        """Pheno tool download."""
        data = expand_gene_set(parse_query_params(request.data))

        if not user_has_permission(
            self.instance_id, request.user, data["datasetId"],
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        study_wrapper = self.gpf_instance.get_wdae_wrapper(data["datasetId"])
        if study_wrapper is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if study_wrapper.is_phenotype:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data["effectTypes"] = EffectTypesMixin.build_effect_types_list(
            data["effectTypes"],
        )

        data["phenoFilterFamilyIds"] = None
        if data.get("familyFilters") is not None:
            data["phenoFilterFamilyIds"] = list(
                self.query_transformer  # noqa: SLF001
                ._transform_filters_to_ids(
                    data["familyFilters"],
                    study_wrapper,
                ),
            )
        if data.get("familyPhenoFilters") is not None:
            data["phenoFilterFamilyIds"] = list(
                self.query_transformer  # noqa: SLF001
                ._transform_pheno_filters_to_ids(
                    data["familyPhenoFilters"],
                    study_wrapper,
                ),
            )

        adapter = cast(
            PhenoToolAdapter,
            self.gpf_instance.get_pheno_tool_adapter(
                study_wrapper,
            ),
        )
        print("adapter finished")

        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            self.generate_columns(
                data,
                adapter,
            ),
            content_type="text/csv",
        )
        response[
            "Content-Disposition"
        ] = "attachment; filename=pheno_report.csv"
        response["Expires"] = "0"
        return response


class PhenoToolPeopleValues(QueryBaseView, DatasetAccessRightsView):
    """View for returning person phenotype data."""

    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        res_df = dataset.phenotype_data.get_people_measure_values_df(
            data["measureIds"],
            data.get("personIds", None),
            data.get("familyIds", None),
            data.get("roles", None),
        )

        result: list[dict[str, Any]] = cast(
            list[dict[str, Any]], res_df.to_dict("records"))

        for v in result:
            v["status"] = str(v["status"])
            v["role"] = str(v["role"])
            v["sex"] = str(v["sex"])

        return Response(result)


class PhenoToolMeasure(QueryBaseView, DatasetAccessRightsView):

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        measure_id = params.get("measureId", None)
        if not measure_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not dataset.phenotype_data.has_measure(measure_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_measure(
            measure_id,
        )

        return Response(result.to_json())


class PhenoToolMeasures(QueryBaseView, DatasetAccessRightsView):

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = params.get("instrument", None)

        if instrument and instrument not in dataset.phenotype_data.instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        measure_type = params.get("measureType", None)
        if measure_type is not None:
            measure_type = MeasureType.from_str(measure_type)

        result = dataset.phenotype_data.get_measures(
            instrument,
            measure_type,
        )

        return Response([m.to_json() for m in result.values()])


class PhenoToolInstruments(QueryBaseView, DatasetAccessRightsView):

    def measure_to_json(self, measure: Measure) -> dict:
        return {
            "measureId": measure.measure_id,
            "instrumentName": measure.instrument_name,
            "measureName": measure.measure_name,
            "measureType": str(measure.measure_type),
            "description": measure.description,
            "defaultFilter": measure.default_filter,
            "valuesDomain": measure.values_domain,
            "minValue":
                None if math.isnan(measure.min_value)  # type: ignore
                else measure.min_value,
            "maxValue":
                None if math.isnan(measure.max_value)  # type: ignore
                else measure.max_value,
        }

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or not dataset.has_pheno_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = dataset.phenotype_data.instruments

        result = {}

        for i in instruments.values():
            result[i.instrument_name] = {
                "name": i.instrument_name,
                "measures": [
                    self.measure_to_json(m) for m in i.measures.values()
                ],
            }

        return Response(result)
