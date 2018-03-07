'''
Created on Feb 16, 2017

@author: lubo
'''
from __future__ import print_function

import ast
from copy import deepcopy
from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse
import itertools
from django.utils.http import urlencode

from preloaded import register
from datasets_api.permissions import IsDatasetAllowed
from users_api.authentication import SessionAuthenticationWithoutCSRF


class GeneSetsBaseView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        self.gscs = register.get('gene_sets_collections')

    @classmethod
    def permitted_datasets(cls, dataset_ids, user):
        return filter(
            lambda dataset_id: IsDatasetAllowed.user_has_permission(
                user, dataset_id),
            dataset_ids)

    @classmethod
    def permitted_denovo_gene_sets_types(cls, gene_sets_types, user):
        if type(gene_sets_types) is list:
            permitted_datasets = cls.permitted_datasets(
                {gene_set_type['datasetId']
                    for gene_set_type in gene_sets_types},
                user)
            return filter(lambda gene_set_type:
                          gene_set_type['datasetId'] in permitted_datasets,
                          gene_sets_types)
        elif type(gene_sets_types) is dict:
            permitted_datasets = cls.permitted_datasets(
                set(gene_sets_types.keys()), user)
            return {k: v
                    for k, v in gene_sets_types.iteritems()
                    if k in permitted_datasets}
        else:
            raise ValueError()


class GeneSetsCollectionsView(GeneSetsBaseView):

    def __init__(self):
        super(GeneSetsCollectionsView, self).__init__()

    def get(self, request):
        gene_sets_collections = deepcopy(self.gscs.get_gene_sets_collections())

        for gene_sets_collection in gene_sets_collections:
            if gene_sets_collection['name'] == 'denovo':
                permitted_types = self.permitted_denovo_gene_sets_types(
                    gene_sets_collection['types'], request.user)
                gene_sets_collection['types'] = permitted_types
                break

        return Response(gene_sets_collections, status=status.HTTP_200_OK)


class GeneSetsView(GeneSetsBaseView):
    """
        {
        "geneSetsCollection": "main",
        "geneSetsTypes": {
            "SD": ["autism", "epilepsy"],
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

        if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'geneSetsTypes' in data:
            gene_sets_types = self.permitted_denovo_gene_sets_types(
                data['geneSetsTypes'], request.user)
        else:
            gene_sets_types = []

        gene_sets = self.gscs.get_gene_sets(
            gene_sets_collection_id, gene_sets_types)

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
            "SD": ["autism", "epilepsy"]
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

        if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'geneSetsTypes' in data:
            gene_sets_types = self.permitted_denovo_gene_sets_types(
                data['geneSetsTypes'], user)
        else:
            gene_sets_types = []

        gene_set = self.gscs.get_gene_set(
            gene_sets_collection_id,
            gene_set_id,
            gene_sets_types
        )
        if gene_set is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = map(lambda s: "{}\r\n".format(s), gene_set['syms'])
        title = '"{}: {}"\r\n'.format(gene_set['name'], gene_set['desc'])
        result = itertools.chain([title], gene_syms)

        response = StreamingHttpResponse(
            result,
            content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=geneset.csv'
        response['Expires'] = '0'

        return response

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in data.items()}
        if 'geneSetsTypes' in res:
            res['geneSetsTypes'] = ast.literal_eval(res['geneSetsTypes'])
        return res

    def get(self, request):
        data = self._parse_query_params(request.query_params)
        return self._build_response(data, request.user)
