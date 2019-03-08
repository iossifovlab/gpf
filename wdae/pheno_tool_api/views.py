from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users_api.authentication import SessionAuthenticationWithoutCSRF
from rest_framework.exceptions import NotAuthenticated
import traceback
from pheno_tool.tool import PhenoTool
from pheno_tool_api.genotype_helper import GenotypeHelper
from functools import partial
from django.http.response import StreamingHttpResponse
import json
from pheno.common import Role, Gender
import logging
from gene_sets.expand_gene_set_decorator import expand_gene_set
from functools import reduce

from datasets_api.studies_manager import get_studies_manager 

logger = logging.getLogger(__name__)


class PhenoToolView(APIView):

    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        datasets_facade = get_studies_manager().get_dataset_facade()
        self._dataset_facade = datasets_facade

    @classmethod
    def get_result_by_gender(cls, result, gender):
        return {
            "negative": {
                "count": result[gender].negative_count,
                "deviation": result[gender].negative_deviation,
                "mean": result[gender].negative_mean
            },
            "positive": {
                "count": result[gender].positive_count,
                "deviation": result[gender].positive_deviation,
                "mean": result[gender].positive_mean
            },
            "pValue": result[gender].pvalue
        }

    @classmethod
    def calc_by_effect(cls, effect, tool, data, dataset):
        data['effectTypes'] = [effect]

        variants = dataset.get_variants(safe=True, **data)
        variants_df = GenotypeHelper.to_persons_variants_df(variants)

        result = tool.calc(variants_df, gender_split=True)
        return {
            "effect": effect,
            "maleResults": cls.get_result_by_gender(result, Gender.M.name),
            "femaleResults": cls.get_result_by_gender(result, Gender.F.name),
        }

    def get_normalize_measure_id(
            self, measure_id, normalize_by, pheno_reg):
        if normalize_by == "non-verbal iq":
            return pheno_reg.get_nonverbal_iq_measure_id(measure_id)
        elif normalize_by == "age":
            return pheno_reg.get_age_measure_id(measure_id)

    def prepare_pheno_tool(self, data):
        dataset_id = data['datasetId']
        measure_id = data['measureId']
        dataset = self.dataset_facade.get_dataset(dataset_id)
        normalize_by = [
            self.get_normalize_measure_id(
                measure_id,
                normalize_by_elem,
                dataset.pheno_reg)
            for normalize_by_elem in data['normalizeBy']
        ]
        normalize_by = [n for n in normalize_by if n is not None]

        tool = PhenoTool(
            dataset.pheno_db, dataset.studies, roles=[Role.prb],
            measure_id=measure_id, normalize_by=normalize_by
        )

        return dataset, tool, normalize_by

    @staticmethod
    def _align_NA_results(results):
        for result in results:
            for gender in ['femaleResults', 'maleResults']:
                res = result[gender]
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
            return "{} ~ {}".format(
                measure_id,
                " + ".join(normalize_by)
            )

    @expand_gene_set
    def post(self, request):
        data = request.data
        try:
            dataset, tool, normalize_by = self.prepare_pheno_tool(data)

            results = [self.calc_by_effect(effect, tool, data, dataset)
                       for effect in data['effectTypes']]

            self._align_NA_results(results)
            description = self._build_report_description(
                tool.measure_id, normalize_by)

            response = {
                "description": description,
                "results": results
            }

            return Response(response)

        except NotAuthenticated:
            logger.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoToolDownload(PhenoToolView):
    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert 'queryData' in res
        query = json.loads(res['queryData'])
        return query

    def join_effect_type_df(self, tool, data, dataset, acc, effect):
        data['effectTypes'] = [effect]

        variants = dataset.get_variants(safe=True, **data)
        variants_df = GenotypeHelper.to_persons_variants_df(variants)
        variants_df.rename(columns={'variants': effect}, inplace=True)

        result = acc.join(variants_df, on="person_id")
        result.fillna(0, inplace=True)
        return result

    @expand_gene_set
    def post(self, request):
        data = self._parse_query_params(request.data)
        effectTypes = data['effectTypes']
        try:
            dataset, tool, normalize_by = self.prepare_pheno_tool(data)
            join_func = partial(self.join_effect_type_df, tool, data, dataset)
            result_df = reduce(join_func, effectTypes,
                               tool.list_of_subjects_df())

            if normalize_by != []:
                column_name = "{} ~ {}".format(data['measureId'],
                                               " + ".join(normalize_by))
                result_df.rename(columns={'normalized': column_name},
                                 inplace=True)

            # Select & sort columns for output
            effectTypesCount = len(effectTypes)
            columns = [col
                       for col in result_df.columns.tolist()
                       if col != "normalized" and col != "role"]
            columns[0], columns[1] = columns[1], columns[0]
            columns = columns[:3] + columns[-effectTypesCount:] + \
                columns[3:-effectTypesCount]

            response = StreamingHttpResponse(result_df.to_csv(index=False,
                                                              columns=columns),
                                             content_type='text/csv')
            response['Content-Disposition'] = \
                'attachment; filename=pheno_report.csv'
            response['Expires'] = '0'
            return response

        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
