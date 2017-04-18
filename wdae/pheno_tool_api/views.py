from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users.authentication import SessionAuthenticationWithoutCSRF
from rest_framework.exceptions import NotAuthenticated
import preloaded
import traceback
from pheno_tool.tool import PhenoTool, VT

# Create your views here.
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
    def calc_by_effect(cls, effect, tool, gene_syms_set, query_data):
        gene_syms = []
        if gene_syms_set:
            gene_syms = list(gene_syms_set)

        result = tool.calc(
            VT(
                effect_types=[effect],
                gene_syms=list(gene_syms),
                present_in_child=['autism only', 'autism and unaffected'],
                present_in_parent=query_data['presentInParent']['presentInParent'],
        ), gender_split=True)
        return {
            "effect": effect,
            "maleResults": cls.get_result_by_gender(result, 'M'),
            "femaleResults": cls.get_result_by_gender(result, 'F'),
        }

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
            tool = PhenoTool(
                dataset.pheno_db, dataset.studies, roles=['prb'],
                measure_id=data['measureId'],
            )

            gene_syms = dataset.get_gene_syms(**data)
            results = [self.calc_by_effect(effect, tool, gene_syms, data)
                        for effect in data['effectTypes']];

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
