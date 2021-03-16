import ast
import json
import itertools
from copy import deepcopy

from rest_framework import status
from rest_framework.response import Response

from django.http.response import StreamingHttpResponse
from django.utils.http import urlencode

from query_base.query_base import QueryBaseView


class GeneSetsCollectionsView(QueryBaseView):
    def __init__(self):
        super(GeneSetsCollectionsView, self).__init__()

    def get(self, request):
        permitted_datasets = self.get_permitted_datasets(request.user)
        gene_sets_collections = deepcopy(
            self.gpf_instance.get_gene_sets_collections()
        )
        denovo_gene_sets = deepcopy(
            self.gpf_instance.get_denovo_gene_sets(
                permitted_datasets
            )
        )

        gene_sets_collections[1:1] = denovo_gene_sets
        return Response(gene_sets_collections, status=status.HTTP_200_OK)


class GeneSetsView(QueryBaseView):
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
        url = "gene_sets/gene_set_download"

        if "denovo" in query["geneSetsCollection"]:
            query["geneSetsTypes"] = json.dumps(query["geneSetsTypes"])
            query["geneSetsTypes"] = query["geneSetsTypes"].replace(" ", "")
        return "{}?{}".format(url, urlencode(query))

    def post(self, request):
        data = request.data
        if "geneSetsCollection" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data["geneSetsCollection"]
        gene_sets_types = data.get("geneSetsTypes", dict())

        if "denovo" in gene_sets_collection_id:
            if not self.gpf_instance.has_denovo_gene_sets():
                return Response(status=status.HTTP_404_NOT_FOUND)
            gene_sets = self.gpf_instance.get_all_denovo_gene_sets(
                gene_sets_types, self.get_permitted_datasets(request.user)
            )
        else:
            if not self.gpf_instance.has_gene_set_collection(
                gene_sets_collection_id
            ):
                return Response(status=status.HTTP_404_NOT_FOUND)

            gene_sets = self.gpf_instance.get_all_gene_sets(
                gene_sets_collection_id
            )

        response = gene_sets
        if "filter" in data:
            f = data["filter"].lower()
            response = [
                r
                for r in response
                if f in r["name"].lower() or f in r["desc"].lower()
            ]

        if "limit" in data:
            limit = int(data["limit"])
            response = response[:limit]

        response = [
            {
                "count": gs.count,
                "name": gs.name,
                "desc": gs.desc,
                "download": self._build_download_url(
                    {
                        "geneSetsCollection": gene_sets_collection_id,
                        "geneSet": gs.name,
                        "geneSetsTypes": gene_sets_types,
                    }
                ),
            }
            for gs in response
        ]

        return Response(response, status=status.HTTP_200_OK)


class GeneSetDownloadView(QueryBaseView):
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
        if "geneSetsCollection" not in data or "geneSet" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data["geneSetsCollection"]
        gene_set_id = data["geneSet"]
        gene_sets_types = data.get("geneSetsTypes", dict())

        permitted_datasets = self.get_permitted_datasets(user)

        if "denovo" in gene_sets_collection_id:
            if not self.gpf_instance.has_denovo_gene_sets():
                return Response(status=status.HTTP_404_NOT_FOUND)
            gene_set = self.gpf_instance.get_denovo_gene_set(
                gene_set_id, gene_sets_types, permitted_datasets
            )
        else:
            if not self.gpf_instance.has_gene_set_collection(
                gene_sets_collection_id
            ):
                return Response(
                    {"unknown gene set collection": gene_sets_collection_id},
                    status=status.HTTP_404_NOT_FOUND,
                )

            gene_set = self.gpf_instance.get_gene_set(
                gene_sets_collection_id, gene_set_id,
            )

        if gene_set is None:
            print("GENE SET NOT FOUND", permitted_datasets)
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = ["{}\r\n".format(s) for s in gene_set.syms]
        title = '"{}: {}"\r\n'.format(gene_set.name, gene_set.desc)
        result = itertools.chain([title], gene_syms)

        response = StreamingHttpResponse(result, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=geneset.csv"
        response["Expires"] = "0"

        return response

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        if "geneSetsTypes" in res:
            # FIXME replace usage of literal_eval
            res["geneSetsTypes"] = ast.literal_eval(res["geneSetsTypes"])
        return res

    def get(self, request):
        data = self._parse_query_params(request.query_params)
        return self._build_response(data, request.user)


class GeneSetsHasDenovoView(QueryBaseView):
    def __init__(self):
        super(GeneSetsHasDenovoView, self).__init__()

    def get(self, request):
        if self.gpf_instance.has_denovo_gene_sets():
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
