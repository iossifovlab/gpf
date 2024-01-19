from io import StringIO
import math
import logging

from typing import Dict, List, Optional, Union, cast, Any, Generator

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from django.http.response import StreamingHttpResponse
from studies.study_wrapper import StudyWrapper

from utils.expand_gene_set import expand_gene_set
from utils.query_params import parse_query_params

from query_base.query_base import QueryDatasetView
from datasets_api.permissions import user_has_permission

from dae.pheno.pheno_data import Measure
from dae.pheno_tool.tool import PhenoResult, PhenoTool, PhenoToolHelper
from dae.effect_annotation.effect import EffectTypesMixin

from .pheno_tool_adapter import PhenoToolAdapter, RemotePhenoToolAdapter


logger = logging.getLogger(__name__)


class PhenoToolView(QueryDatasetView):
    """View for returning pheno tool results."""

    @staticmethod
    def get_result_by_sex(
        result: dict[str, PhenoResult],
        sex: str
    ) -> Dict[str, Any]:
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

    # @classmethod
    # def calc_by_effect(
    #     cls, effect: str, tool: PhenoTool, people_variants: Counter
    # ) -> dict:
    #     result = tool.calc(people_variants, sex_split=True)
    #     assert isinstance(result, dict)

    #     return {
    #         "effect": effect,
    #         "maleResults": cls.get_result_by_sex(result, Sex.M.name),
    #         "femaleResults": cls.get_result_by_sex(result, Sex.F.name),
    #     }

    def prepare_pheno_tool_adapter(
        self, data: dict[str, Any]
    ) -> Optional[PhenoToolAdapter]:
        """Construct pheno tool adapter."""
        study_wrapper = self.gpf_instance.get_wdae_wrapper(data["datasetId"])
        if not (
            study_wrapper
            and study_wrapper.phenotype_data is not None
            and study_wrapper.phenotype_data.has_measure(data["measureId"])
        ):
            return None

        if study_wrapper.is_remote:
            return RemotePhenoToolAdapter(  # type: ignore
                study_wrapper.rest_client,
                study_wrapper._remote_study_id  # pylint: disable=W0212
            )
        study_wrapper = cast(StudyWrapper, study_wrapper)

        helper = PhenoToolHelper(
            study_wrapper, study_wrapper.phenotype_data  # type: ignore
        )

        family_filters = data.get("familyFilters")
        if family_filters is None:
            pheno_filter_family_ids = None
        else:
            # pylint: disable=protected-access
            pheno_filter_family_ids = list(
                study_wrapper
                .query_transformer
                ._transform_filters_to_ids(family_filters))

        study_persons = helper.genotype_data_persons(data.get("familyIds", []))

        person_ids = set(study_persons)

        tool = PhenoTool(
            helper.phenotype_data,
            measure_id=data["measureId"],
            person_ids=list(person_ids),
            family_ids=pheno_filter_family_ids,
            normalize_by=data["normalizeBy"],
        )
        return PhenoToolAdapter(study_wrapper, tool, helper)

    @staticmethod
    def _build_report_description(
        measure_id: str,
        normalize_by: List[Union[str, Any]]
    ) -> str:
        if not normalize_by:
            return measure_id
        normalize_desc = " + ".join(normalize_by)
        return f"{measure_id} ~ {normalize_desc}"

    def post(self, request: Request) -> Response:
        """Return pheno tool results based on POST request."""
        data = expand_gene_set(request.data, request.user)
        adapter = self.prepare_pheno_tool_adapter(data)

        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)
        effect_groups = list(data["effectTypes"])
        data = cast(StudyWrapper, adapter.helper.genotype_data) \
            .transform_request(data)
        result = adapter.calc_variants(data, effect_groups)

        return Response(result)


class PhenoToolDownload(PhenoToolView):
    """Pheno tool download view."""

    def generate_columns(
            self,
            adapter: PhenoToolAdapter,
            data: dict
    ) -> Generator[str, None, None]:
        """Pheno tool download generator function."""
        # Return a response instantly and make download more responsive
        yield ""

        data["effectTypes"] = EffectTypesMixin.build_effect_types_list(
            data["effectTypes"]
        )
        effect_groups = list(data["effectTypes"])

        data = cast(StudyWrapper, adapter.helper.genotype_data) \
            .transform_request(data)
        tool = adapter.pheno_tool

        result_df = tool.pheno_df.copy()
        variants = adapter.helper.genotype_data_variants(data, effect_groups)

        for effect in effect_groups:
            result_df = PhenoTool.join_pheno_df_with_variants(
                result_df, variants[effect]
            )
            result_df = result_df.rename(columns={"variant_count": effect})

        if tool.normalize_by:
            column_name = self._build_report_description(
                tool.measure_id, tool.normalize_by
            )
            result_df = result_df.rename(columns={"normalized": column_name})
            result_df[column_name] = result_df[column_name].round(decimals=5)

        result_df[tool.measure_id] = \
            result_df[tool.measure_id].round(decimals=5)

        columns = [
            col
            for col in result_df.columns.tolist()
            if col not in {"normalized", "role"}
        ]

        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False, columns=columns)
        csv_buffer.seek(0)
        for row in csv_buffer.readlines():
            yield row

    def post(self, request: Request) -> Response:
        """Pheno tool download."""
        data = expand_gene_set(parse_query_params(request.data), request.user)

        if not user_has_permission(
            self.instance_id, request.user, data["datasetId"]
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        adapter = self.prepare_pheno_tool_adapter(data)
        print("adapter finished")

        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            self.generate_columns(adapter, data),
            content_type="text/csv",
        )
        response[
            "Content-Disposition"
        ] = "attachment; filename=pheno_report.csv"
        response["Expires"] = "0"
        return response


class PhenoToolPersons(QueryDatasetView):

    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_persons(
            data.get("roles", None),
            data.get("personIds", None),
            data.get("familyIds", None),
        )

        response: dict[str, Any] = {}
        for key in result.keys():
            person = result[key]
            response[key] = {
                "person_id": person.person_id,
                "family_id": person.family_id,
                "role": str(person.role),
                "sex": str(person.sex),
                "status": str(person.status),
            }

        return Response(response)


class PhenoToolPersonsValues(QueryDatasetView):
    """View for returning person phenotype data."""

    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        res_df = dataset.phenotype_data.get_persons_values_df(
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


class PhenoToolMeasure(QueryDatasetView):

    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
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


class PhenoToolMeasures(QueryDatasetView):

    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument = params.get("instrument", None)

        if instrument and instrument not in dataset.phenotype_data.instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        measure_type = params.get("measureType", None)

        result = dataset.phenotype_data.get_measures(
            instrument,
            measure_type,
        )

        return Response([m.to_json() for m in result.values()])


class PhenoToolMeasureValues(QueryDatasetView):
    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_measure_values(
            data["measureId"],
            data.get("personIds", None),
            data.get("familyIds", None),
            data.get("roles", None),
            data.get("defaultFilter", "skip"),
        )

        return Response(result)


class PhenoToolValues(QueryDatasetView):
    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_values_df(
            data["measureIds"],
            data.get("personIds", None),
            data.get("familyIds", None),
            data.get("roles", None),
            data.get("defaultFilter", "apply"),
        )

        return Response(result.to_dict("records"))


class PhenoToolInstruments(QueryDatasetView):

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
                else measure.max_value
        }

    def get(self, request: Request) -> Response:
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instruments = dataset.phenotype_data.instruments

        result = dict()

        for i in instruments.values():
            result[i.instrument_name] = {
                "name": i.instrument_name,
                "measures": [
                    self.measure_to_json(m) for m in i.measures.values()
                ]
            }

        return Response(result)


class PhenoToolInstrumentValues(QueryDatasetView):

    def post(self, request: Request) -> Response:
        data = request.data
        dataset_id = data["datasetId"]
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset or dataset.phenotype_data is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument_name = data["instrumentName"]

        instruments = dataset.phenotype_data.instruments

        if instrument_name not in instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_instrument_values(
            instrument_name,
            data.get("personIds", None),
            data.get("familyIds", None),
            data.get("roles", None),
            data.get("measures", None)
        )

        return Response(result)
