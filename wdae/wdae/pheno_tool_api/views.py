import json
import logging
from collections import Counter

from rest_framework.response import Response
from rest_framework import status

from django.http.response import StreamingHttpResponse

from gene_sets.expand_gene_set_decorator import expand_gene_set

from dae.pheno_tool.tool import PhenoTool, PhenoToolHelper
from dae.variants.attributes import Sex

from query_base.query_base import QueryBaseView


logger = logging.getLogger(__name__)


class PhenoToolView(QueryBaseView):

    @staticmethod
    def get_result_by_sex(result, sex):
        return {
            "negative": {
                "count": result[sex].negative_count,
                "deviation": result[sex].negative_deviation,
                "mean": result[sex].negative_mean
            },
            "positive": {
                "count": result[sex].positive_count,
                "deviation": result[sex].positive_deviation,
                "mean": result[sex].positive_mean
            },
            "pValue": result[sex].pvalue
        }

    @classmethod
    def calc_by_effect(cls, effect, tool, people_variants):
        result = tool.calc(people_variants, sex_split=True)
        return {
            "effect": effect,
            "maleResults": cls.get_result_by_sex(result, Sex.M.name),
            "femaleResults": cls.get_result_by_sex(result, Sex.F.name),
        }

    def prepare_pheno_tool(self, data):
        study_wrapper = self.variants_db.get_wdae_wrapper(data['datasetId'])

        if not (study_wrapper and
                study_wrapper.phenotype_data.has_measure(data['measureId'])):
            return None, None

        helper = PhenoToolHelper(study_wrapper)

        pheno_filter_persons = \
            helper.pheno_filter_persons(data.get('phenoFilters'))
        study_persons = helper.genotype_data_persons(data.get('familyIds', []))

        person_ids = set(study_persons)
        if pheno_filter_persons:
            person_ids &= set(pheno_filter_persons)

        tool = PhenoTool(
            helper.genotype_data.phenotype_data,
            measure_id=data['measureId'],
            person_ids=person_ids,
            normalize_by=data['normalizeBy']
        )
        return helper, tool

    @staticmethod
    def _align_NA_results(results):
        for result in results:
            for sex in ['femaleResults', 'maleResults']:
                res = result[sex]
                if res['positive']['count'] == 0:
                    assert res['positive']['mean'] == 0
                    assert res['positive']['deviation'] == 0
                    assert res['pValue'] == 'NA'
                    res['positive']['mean'] = res['negative']['mean']
                if res['negative']['count'] == 0:
                    assert res['negative']['mean'] == 0
                    assert res['negative']['deviation'] == 0
                    assert res['pValue'] == 'NA'
                    res['negative']['mean'] = res['positive']['mean']

    @staticmethod
    def _build_report_description(measure_id, normalize_by):
        if not normalize_by:
            return measure_id
        else:
            return "{} ~ {}".format(measure_id, " + ".join(normalize_by))

    @expand_gene_set
    def post(self, request):
        data = request.data
        helper, tool = self.prepare_pheno_tool(data)

        if not (helper and tool):
            return Response(status=status.HTTP_404_NOT_FOUND)

        people_variants = helper.genotype_data_variants(data)

        results = [self.calc_by_effect(effect, tool,
                   people_variants.get(effect.lower(), Counter()))
                   for effect in data['effectTypes']]
        self._align_NA_results(results)

        response = {
            "description": self._build_report_description(
                tool.measure_id, tool.normalize_by),
            "results": results
        }
        return Response(response)


class PhenoToolDownload(PhenoToolView):

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert 'queryData' in res
        query = json.loads(res['queryData'])
        return query

    @expand_gene_set
    def post(self, request):
        data = self._parse_query_params(request.data)
        helper, tool = self.prepare_pheno_tool(data)

        result_df = tool.pheno_df.copy()
        variants = helper.genotype_data_variants(data)

        for effect in data['effectTypes']:
            result_df = PhenoTool.join_pheno_df_with_variants(
                result_df, variants[effect.lower()])
            result_df = result_df.rename(
                columns={'variant_count': effect})

        if tool.normalize_by:
            column_name = \
                self._build_report_description(tool.measure_id,
                                               tool.normalize_by)
            result_df = result_df.rename(
                columns={'normalized': column_name})

        # Select & sort columns for output
        effectTypesCount = len(data['effectTypes'])
        columns = [col
                   for col in result_df.columns.tolist()
                   if col != "normalized" and col != "role"]
        columns[0], columns[1] = columns[1], columns[0]
        columns = columns[:3] + columns[-effectTypesCount:] + \
            columns[3:-effectTypesCount]

        response = StreamingHttpResponse(
            result_df.to_csv(index=False, columns=columns),
            content_type='text/csv'
        )
        response['Content-Disposition'] = \
            'attachment; filename=pheno_report.csv'
        response['Expires'] = '0'
        return response
