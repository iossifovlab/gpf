'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
import ast
from copy import deepcopy
from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse
import itertools
from django.utils.http import urlencode

from datasets_api.studies_manager import get_studies_manager
from datasets_api.permissions import IsDatasetAllowed
from users_api.authentication import SessionAuthenticationWithoutCSRF


class GeneSetsBaseView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.gscs = get_studies_manager().get_gene_sets_collections()
        self.dgscf = \
            get_studies_manager().get_denovo_gene_set_collection_facade()
        print("datasets loaded in view")


class GeneSetsCollectionsView(GeneSetsBaseView):

    def __init__(self):
        super(GeneSetsCollectionsView, self).__init__()

    def get(self, request):
        permitted_datasets = IsDatasetAllowed.permitted_datasets(request.user)
        gene_sets_collections = deepcopy(
            self.gscs.get_collections_descriptions(permitted_datasets))
        denovo_gene_sets_collections = deepcopy(
            self.dgscf.get_collections_descriptions(permitted_datasets))

        gene_sets_collections[1:1] = [denovo_gene_sets_collections]
        return Response(gene_sets_collections, status=status.HTTP_200_OK)


class GeneSetsView(GeneSetsBaseView):
    """
        {
        "geneSetsCollection": "main",
        "geneSetsTypes": {
            "SD_TEST": ["autism", "epilepsy"],
        },
        "filter": "ivan",
        "limit": 100
        }
    """
    def __init__(self):
        super(GeneSetsView, self).__init__()

    @staticmethod
    def _build_download_url(query):
        url = 'gene_sets/gene_set_download'
        return '{}?{}'.format(url, urlencode(query))

    # @profile('/home/lubo/gene_sets.prof')
    def post(self, request):
        data = request.data
        if 'geneSetsCollection' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data['geneSetsCollection']
        gene_sets_types = data.get('geneSetsTypes', [])

        if gene_sets_collection_id == 'denovo':
            if not self.dgscf.has_denovo_gene_set(gene_sets_collection_id):
                return Response(status=status.HTTP_404_NOT_FOUND)

            gene_sets = self.dgscf.get_denovo_gene_sets(
                gene_sets_collection_id, gene_sets_types,
                IsDatasetAllowed.permitted_datasets(request.user))

        else:
            if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
                return Response(status=status.HTTP_404_NOT_FOUND)

            gene_sets = self.gscs.get_gene_sets(
                gene_sets_collection_id, gene_sets_types,
                IsDatasetAllowed.permitted_datasets(request.user))

        response = gene_sets
        if 'filter' in data:
            f = data['filter'].lower()
            response = [
                r for r in response
                if f in r['name'].lower() or f in r['desc'].lower()
            ]

        if 'limit' in data:
            limit = int(data['limit'])
            response = response[:limit]

        response = [
            {
                'count': gs['count'],
                'name': gs['name'],
                'desc': gs['desc'],
                'download': self._build_download_url({
                    'geneSetsCollection': gene_sets_collection_id,
                    'geneSet': gs['name'],
                    'geneSetsTypes': gene_sets_types
                })
            }
            for gs in response
        ]

        return Response(response, status=status.HTTP_200_OK)


class GeneSetDownloadView(GeneSetsBaseView):
    """
        {
        "geneSetsCollection": "denovo",
        "geneSet": "LGDs",
        "geneSetsTypes": {
            "SD_TEST": {"phenotype": ["autism", "epilepsy"]}
        }
        }
    """

    def __init__(self):
        super(GeneSetDownloadView, self).__init__()

    def post(self, request):
        return self._build_response(request.data, request.user)

    def _build_response(self, data, user):
        if 'geneSetsCollection' not in data or 'geneSet' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data['geneSetsCollection']
        gene_set_id = data['geneSet']
        gene_sets_types = data.get('geneSetsTypes', {})

        permitted_datasets = IsDatasetAllowed.permitted_datasets(user)

        if gene_sets_collection_id == 'denovo':
            if not self.dgscf.has_denovo_gene_set(gene_sets_collection_id):
                return Response(status=status.HTTP_404_NOT_FOUND)

            gene_set = self.dgscf.get_denovo_gene_set(
                gene_sets_collection_id,
                gene_set_id,
                gene_sets_types,
                permitted_datasets
            )

        else:
            if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
                return Response({
                    "unknown gene set collection": gene_sets_collection_id
                }, status=status.HTTP_404_NOT_FOUND)

            gene_set = self.gscs.get_gene_set(
                gene_sets_collection_id,
                gene_set_id,
                gene_sets_types,
                permitted_datasets
            )

        if gene_set is None:
            print("GENE SET NOT FOUND", permitted_datasets)
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = ["{}\r\n".format(s) for s in gene_set['syms']]
        title = '"{}: {}"\r\n'.format(gene_set['name'], gene_set['desc'])
        result = itertools.chain([title], gene_syms)

        response = StreamingHttpResponse(
            result,
            content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=geneset.csv'
        response['Expires'] = '0'

        return response

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        if 'geneSetsTypes' in res:
            res['geneSetsTypes'] = ast.literal_eval(res['geneSetsTypes'])
        return res

    def get(self, request):
        data = self._parse_query_params(request.query_params)
        return self._build_response(data, request.user)
