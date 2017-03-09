'''
Created on Feb 16, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from gene.gene_set_collections import GeneSetsCollections
from django.http.response import StreamingHttpResponse
import itertools
from django.utils.http import urlencode


class GeneSetsCollectionsView(views.APIView):

    def __init__(self):
        self.gscs = GeneSetsCollections()

    def get(self, request):
        response = self.gscs.get_gene_sets_collections()
        return Response(response, status=status.HTTP_200_OK, )


class GeneSetsView(views.APIView):
    """
        {
        "geneSetsCollection": "main",
        "geneSetsTypes": ["autism", "epilepsy"],
        "filter": "ivan",
        "limit": 100
        }
    """

    def __init__(self):
        self.gscs = GeneSetsCollections()

    @staticmethod
    def _build_download_url(query):
        url = 'gene_sets/gene_set_download'
        return '{}?{}'.format(url, urlencode(query))

    def post(self, request):
        data = request.data
        if 'geneSetsCollection' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data['geneSetsCollection']

        if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'geneSetsTypes' in data:
            gene_sets_types = data['geneSetsTypes']
        else:
            gene_sets_types = []

        gene_sets = self.gscs.get_gene_sets(
            gene_sets_collection_id, gene_sets_types)

        response = [
            {
                'count': gs['count'],
                'name': gs['name'],
                'desc': gs['desc'],
                'download': self._build_download_url({
                    'geneSetsCollection': gene_sets_collection_id,
                    'geneSet': gs['name'],
                    'geneSetsTypes': ','.join(gene_sets_types)
                })
            }
            for gs in gene_sets
        ]
        if 'filter' in data:
            f = data['filter'].lower()
            response = [
                r for r in response
                if f in r['name'].lower() or f in r['desc'].lower()
            ]

        if 'limit' in data:
            limit = int(data['limit'])
            response = response[:limit]

        return Response(response, status=status.HTTP_200_OK)


class GeneSetDownloadView(views.APIView):
    """
        {
        "geneSetsCollection": "denovo",
        "geneSet": "LGDs",
        "geneSetsTypes": ["autism", "epilepsy"]
        }
    """

    def __init__(self):
        self.gscs = GeneSetsCollections()

    def post(self, request):
        data = request.data
        return self._build_response(data)

    def _build_response(self, data):
        if 'geneSetsCollection' not in data or 'geneSet' not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data['geneSetsCollection']
        gene_set_id = data['geneSet']

        if not self.gscs.has_gene_sets_collection(gene_sets_collection_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'geneSetsTypes' in data:
            gene_sets_types = data['geneSetsTypes']
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
        print(data)
        res = {str(k): str(v) for k, v in data.items()}
        if 'geneSetsTypes' in res:
            res['geneSetsTypes'] = res['geneSetsTypes'].split(',')
        print(res)
        return res

    def get(self, request):
        data = self._parse_query_params(request.query_params)
        return self._build_response(data)
