import json
import math
import logging

from rest_framework.response import Response  # type: ignore
from rest_framework import status  # type: ignore

from django.http.response import StreamingHttpResponse

from gene_sets.expand_gene_set_decorator import expand_gene_set

from query_base.query_base import QueryBaseView
from datasets_api.permissions import user_has_permission

from dae.pheno_tool.tool import PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex

from .pheno_tool_adapter import PhenoToolAdapter, RemotePhenoToolAdapter


logger = logging.getLogger(__name__)


class PhenoToolView(QueryBaseView):
    @staticmethod
    def get_result_by_sex(result, sex):
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

    @classmethod
    def calc_by_effect(cls, effect, tool, people_variants):
        result = tool.calc(people_variants, sex_split=True)
        return {
            "effect": effect,
            "maleResults": cls.get_result_by_sex(result, Sex.M.name),
            "femaleResults": cls.get_result_by_sex(result, Sex.F.name),
        }

    def prepare_pheno_tool_adapter(self, data):
        study_wrapper = self.gpf_instance.get_wdae_wrapper(data["datasetId"])
        if not (
            study_wrapper
            and study_wrapper.phenotype_data.has_measure(data["measureId"])
        ):
            return None

        if study_wrapper.is_remote:
            return RemotePhenoToolAdapter(
                study_wrapper.rest_client,
                study_wrapper._remote_study_id
            )

        helper = PhenoToolHelper(study_wrapper, study_wrapper.phenotype_data)

        family_filters = data.get("familyFilters")
        if family_filters is None:
            pheno_filter_family_ids = None
        else:
            pheno_filter_family_ids = study_wrapper\
                .query_transformer\
                ._transform_filters_to_ids(family_filters)

        study_persons = helper.genotype_data_persons(data.get("familyIds", []))

        person_ids = set(study_persons)

        tool = PhenoTool(
            helper.phenotype_data,
            measure_id=data["measureId"],
            person_ids=person_ids,
            family_ids=pheno_filter_family_ids,
            normalize_by=data["normalizeBy"],
        )
        return PhenoToolAdapter(study_wrapper, tool, helper)

    @staticmethod
    def _build_report_description(measure_id, normalize_by):
        if not normalize_by:
            return measure_id
        else:
            return "{} ~ {}".format(measure_id, " + ".join(normalize_by))

    @expand_gene_set
    def post(self, request):
        data = request.data
        adapter = self.prepare_pheno_tool_adapter(data)

        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)
        effect_groups = [effect for effect in data["effectTypes"]]
        data = adapter.helper.genotype_data.transform_request(data)
        result = adapter.calc_variants(data, effect_groups)

        return Response(result)


class PhenoToolDownload(PhenoToolView):
    @expand_gene_set
    def post(self, request):
        data = request.data
        adapter = self.prepare_pheno_tool_adapter(data)
        if not adapter:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user_has_permission(request.user, data["datasetId"]):
            return Response(status=status.HTTP_403_FORBIDDEN)

        effect_groups = [effect for effect in data["effectTypes"]]

        data = adapter.helper.genotype_data.transform_request(data)
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

        # Select & sort columns for output
        effect_types_count = len(data["effect_types"])
        columns = [
            col
            for col in result_df.columns.tolist()
            if col != "normalized" and col != "role"
        ]
        columns[0], columns[1] = columns[1], columns[0]
        columns = (
            columns[:3]
            + columns[-effect_types_count:]
            + columns[3:-effect_types_count]
        )

        response = StreamingHttpResponse(
            result_df.to_csv(index=False, columns=columns),
            content_type="text/csv",
        )
        response[
            "Content-Disposition"
        ] = "attachment; filename=pheno_report.csv"
        response["Expires"] = "0"
        return response


class PhenoToolPersons(QueryBaseView):
    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_persons(
            data["roles"],
            data["personIds"],
            data["familyIds"],
        )

        for key in result.keys():
            person = result[key]
            result[key] = {
                "person_id": person.person_id,
                "family_id": person.family_id,
                "role": str(person.role),
                "sex": str(person.sex),
                "status": str(person.status),
            }

        return Response(result)


class PhenoToolPersonsValues(QueryBaseView):

    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_persons_values_df(
            data["measureIds"],
            data["personIds"],
            data["familyIds"],
            data["roles"],
        )

        result = result.to_dict("records")

        for v in result:
            v["status"] = str(v["status"])
            v["role"] = str(v["role"])
            v["sex"] = str(v["sex"])

        return Response(result)


class PhenoToolMeasure(QueryBaseView):
    def get(self, request):
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
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


class PhenoToolMeasures(QueryBaseView):
    def get(self, request):
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
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


class PhenoToolMeasureValues(QueryBaseView):
    def post(self, request):
        data = request.data
        print(data)
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_measure_values(
            data["measureId"],
            data["personIds"],
            data["familyIds"],
            data["roles"],
            data["defaultFilter"],
        )

        return Response(result)


class PhenoToolValues(QueryBaseView):
    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_values_df(
            data["measureIds"],
            data["personIds"],
            data["familyIds"],
            data["roles"],
            data["defaultFilter"],
        )

        return Response(result.to_dict("records"))


class PhenoToolInstruments(QueryBaseView):

    def measure_to_json(self, measure):
        return {
            "measureId": measure.measure_id,
            "instrumentName": measure.instrument_name,
            "measureName": measure.measure_name,
            "measureType": str(measure.measure_type),
            "description": measure.description,
            "defaultFilter": measure.default_filter,
            "valuesDomain": measure.values_domain,
            "minValue":
                None if math.isnan(measure.min_value) else measure.min_value,
            "maxValue":
                None if math.isnan(measure.max_value) else measure.max_value
        }

    def get(self, request):
        params = request.GET
        dataset_id = params.get("datasetId", None)
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
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


class PhenoToolInstrumentValues(QueryBaseView):
    def post(self, request):
        data = request.data
        dataset_id = data["datasetId"]
        if not dataset_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        instrument_name = data["instrumentName"]

        instruments = dataset.phenotype_data.instruments

        if instrument_name not in instruments:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = dataset.phenotype_data.get_instrument_values(
            instrument_name,
            data["personIds"],
            data["familyIds"],
            data["roles"],
            data.get("measures")
        )

        return Response(result)
