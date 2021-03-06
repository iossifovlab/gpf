import json
import math
import logging

from rest_framework.response import Response
from rest_framework import status

from django.http.response import StreamingHttpResponse

from gene_sets.expand_gene_set_decorator import expand_gene_set

from dae.pheno_tool.tool import PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex

from query_base.query_base import QueryBaseView

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

        helper = PhenoToolHelper(study_wrapper)

        pheno_filter_family_ids = helper.pheno_filter_persons(
            data.get("phenoFilters")
        )
        study_persons = helper.genotype_data_persons(data.get("familyIds", []))

        person_ids = set(study_persons)

        tool = PhenoTool(
            helper.genotype_data.phenotype_data,
            measure_id=data["measureId"],
            person_ids=person_ids,
            family_ids=pheno_filter_family_ids,
            normalize_by=data["normalizeBy"],
        )
        return PhenoToolAdapter(tool, helper)

    @staticmethod
    def _align_NA_results(results):
        for result in results:
            for sex in ["femaleResults", "maleResults"]:
                res = result[sex]
                if res["positive"]["count"] == 0:
                    assert res["positive"]["mean"] == 0
                    assert res["positive"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["positive"]["mean"] = res["negative"]["mean"]
                if res["negative"]["count"] == 0:
                    assert res["negative"]["mean"] == 0
                    assert res["negative"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["negative"]["mean"] = res["positive"]["mean"]

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

        result = adapter.calc_variants(data)

        return Response(result)


class PhenoToolDownload(PhenoToolView):
    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert "queryData" in res
        query = json.loads(res["queryData"])
        return query

    @expand_gene_set
    def post(self, request):
        data = self._parse_query_params(request.data)
        helper, tool = self.prepare_pheno_tool(data)

        result_df = tool.pheno_df.copy()
        variants = helper.genotype_data_variants(data)

        for effect in data["effectTypes"]:
            result_df = PhenoTool.join_pheno_df_with_variants(
                result_df, variants[effect.lower()]
            )
            result_df = result_df.rename(columns={"variant_count": effect})

        if tool.normalize_by:
            column_name = self._build_report_description(
                tool.measure_id, tool.normalize_by
            )
            result_df = result_df.rename(columns={"normalized": column_name})

        # Select & sort columns for output
        effectTypesCount = len(data["effectTypes"])
        columns = [
            col
            for col in result_df.columns.tolist()
            if col != "normalized" and col != "role"
        ]
        columns[0], columns[1] = columns[1], columns[0]
        columns = (
            columns[:3]
            + columns[-effectTypesCount:]
            + columns[3:-effectTypesCount]
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
        if not measure_type:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
        )

        return Response(result)
