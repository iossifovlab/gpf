from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users_api.authentication import SessionAuthenticationWithoutCSRF
from rest_framework.exceptions import NotAuthenticated
import preloaded
import traceback
from pheno_tool.tool import PhenoTool
from pheno_tool_api.genotype_helper import GenotypeHelper
import pandas as pd
from functools import partial


class PhenoToolView(APIView):

    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

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
            "maleResults": cls.get_result_by_gender(result, 'M'),
            "femaleResults": cls.get_result_by_gender(result, 'F'),
        }

    def get_normalize_measure_id(self, measure_id, normalize_by, pheno_db):
        if normalize_by == "non-verbal iq":
            return pheno_db.get_nonverbal_iq_measure_id(measure_id)
        elif normalize_by == "age":
            return pheno_db.get_age_measure_id(measure_id)

    def prepare_pheno_tool(self, data):
        dataset_id = data['datasetId']
        measure_id = data['measureId']
        dataset = self.datasets_factory.get_dataset(dataset_id)
        normalize_by = [self.get_normalize_measure_id(measure_id,
                                                      normalize_by_elem,
                                                      dataset.pheno_db)
                        for normalize_by_elem in data['normalizeBy']]

        tool = PhenoTool(
            dataset.pheno_db, dataset.studies, roles=['prb'],
            measure_id=measure_id, normalize_by=normalize_by
        )

        return dataset, tool

    def post(self, request):
        data = request.data
        try:
            dataset, tool = self.prepare_pheno_tool(data)

            results = [self.calc_by_effect(effect, tool, data, dataset)
                       for effect in data['effectTypes']]

            response = {
                "description": "Desc",
                "results": results
            }

            return Response(response)

        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)


class PhenoToolDownload(PhenoToolView):
    def join_effect_type_df(self, tool, data, dataset, acc, effect):
        data['effectTypes'] = [effect]

        variants = dataset.get_variants(safe=True, **data)
        variants_df = GenotypeHelper.to_persons_variants_df(variants)
        variants_df.rename(columns={'variants': effect}, inplace=True)

        result = acc.join(variants_df, on="person_id")
        result.fillna(0, inplace=True)
        return result

    def post(self, request):
        data = request.data
        try:
            dataset, tool = self.prepare_pheno_tool(data)
            join_func = partial(self.join_effect_type_df, tool, data, dataset)
            results = reduce(join_func, data['effectTypes'],
                             tool.list_of_subjects_df())
            print(results)
            response = {
                "description": "Desc",
                "results": results
            }

            return Response(response)

        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
