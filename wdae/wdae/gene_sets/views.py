"""Classes to handle gene set views."""

import ast
import itertools
import logging
from collections.abc import Sequence
from copy import deepcopy
from typing import Any, cast

from dae.gene_sets.gene_sets_db import GeneSet
from datasets_api.permissions import get_instance_timestamp_etag
from django.http.response import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from utils.gene_sets import get_denovo_gene_set_spec

logger = logging.getLogger(__name__)


class GeneSetsCollectionsView(QueryBaseView):
    """Class to handle gene sets collections view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        """Build response to a get request."""
        gene_sets_collections = deepcopy(
            self.gpf_instance.gene_sets_db.collections_descriptions,
        )
        denovo_gene_sets = deepcopy(
            self.gpf_instance.denovo_gene_sets_db.collections_descriptions,
        )

        gene_sets_collections[1:1] = denovo_gene_sets
        return Response(gene_sets_collections, status=status.HTTP_200_OK)


class DenovoGeneSetsTypesView(QueryBaseView):
    """Class to handle denovo gene sets view."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        """Build response to a get request."""

        dataset_phenotypes = deepcopy(
            self.gpf_instance.denovo_gene_sets_db.denovo_gene_sets_types,
        )

        return Response(dataset_phenotypes, status=status.HTTP_200_OK)


class DenovoGeneSetsDb(QueryBaseView):
    """
    Class to return the entire denovo gene sets db.

    Used for federation remote purposes.
    """

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        """Build response to a get request."""
        result = {}

        for study_id, collection in self.gpf_instance.denovo_gene_sets_db._denovo_gene_set_collections.items():  # noqa: E501, SLF001
            result[study_id] = dict(collection.cache)

        return Response(result, status=status.HTTP_200_OK)


class GeneSetsView(QueryBaseView):
    """Class to handle gene set view.

    {
    "geneSetsCollection": "main",
    "geneSetsTypes": {
        "SD_TEST": ["autism", "epilepsy"],
    },
    "filter": "ivan",
    "limit": 100
    }
    """

    def post(self, request: Request) -> Response:
        """Build response to a post request."""
        if not request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = cast(dict, request.data)
        if "geneSetsCollection" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data["geneSetsCollection"]

        gene_sets_types = get_denovo_gene_set_spec(
            data.get("geneSetsTypes", []),
        )

        gene_sets: Sequence[GeneSet | dict[str, Any]] = []

        if "denovo" in gene_sets_collection_id:
            if not self.gpf_instance.denovo_gene_sets_db.has_gene_sets():
                return Response(status=status.HTTP_404_NOT_FOUND)
            gene_sets = self.gpf_instance.denovo_gene_sets_db.get_all_gene_sets(
                gene_sets_types,
                gene_sets_collection_id,
            )
        else:
            if not self.gpf_instance.gene_sets_db.has_gene_set_collection(
                gene_sets_collection_id,
            ):
                return Response(status=status.HTTP_404_NOT_FOUND)

            gene_sets = self.gpf_instance.gene_sets_db.get_all_gene_sets(
                gene_sets_collection_id,
            )
        logger.debug("gene set collection: %s", gene_sets_collection_id)
        logger.debug("gene sets: %s", len(gene_sets))

        response = gene_sets[:]
        if "filter" in data:
            query = data["filter"].lower()
            response = [
                r
                for r in response
                if query in r["name"].lower() or query in r["desc"].lower()
            ]

        if "limit" in data:
            limit = int(data["limit"])
            response = response[:limit]

        response = [
            {
                "count": gs["count"],
                "name": gs["name"],
                "desc": gs["desc"],
            }
            for gs in response
        ]
        logger.debug("gene sets response: %s", [r["name"] for r in response])
        return Response(response, status=status.HTTP_200_OK)


class GeneSetDownloadView(QueryBaseView):
    """Class to handle gene set download view.

    {
        "geneSetsCollection": "denovo",
        "geneSet": "LGDs",
        "geneSetsTypes": [
            {
                "datasetId": "SD_TEST",
                "collections": [
                    {
                        "personSetId": "phenotype"
                        "types": [
                            "autism",
                            "epilepsy",
                        ]
                    }
                ]
            }
        ]
    }
    """

    def post(self, request: Request) -> Response | StreamingHttpResponse:
        if not request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return self._build_response(cast(dict, request.data))

    def _build_response(
        self, data: dict[str, Any],
    ) -> Response | StreamingHttpResponse:
        if "geneSetsCollection" not in data or "geneSet" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        gene_sets_collection_id = data["geneSetsCollection"]
        gene_set_id = data["geneSet"]
        gene_sets_types = get_denovo_gene_set_spec(
            data.get("geneSetsTypes", []),
        )

        gene_set: GeneSet | dict[str, Any] | None = None

        if "denovo" in gene_sets_collection_id:
            if not self.gpf_instance.denovo_gene_sets_db.has_gene_sets():
                return Response(status=status.HTTP_404_NOT_FOUND)
            gene_set = self.gpf_instance.denovo_gene_sets_db.get_gene_set(
                gene_set_id,
                gene_sets_types,
                gene_sets_collection_id,
            )
        else:
            if not self.gpf_instance.gene_sets_db.has_gene_set_collection(
                gene_sets_collection_id,
            ):
                return Response(
                    {"unknown gene set collection": gene_sets_collection_id},
                    status=status.HTTP_404_NOT_FOUND,
                )

            gene_set = self.gpf_instance.gene_sets_db.get_gene_set(
                gene_sets_collection_id,
                gene_set_id,
            )

        if gene_set is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = [f"{s}\n".encode() for s in gene_set["syms"]]
        result = itertools.chain(
            [
                f"{gene_set['name']}\n".encode(),
                f"{gene_set['desc']}\n".encode(),
            ],
            gene_syms)

        response = StreamingHttpResponse(result, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=geneset.csv"
        response["Expires"] = "0"

        return response

    @staticmethod
    def _parse_query_params(data: dict[str, Any]) -> dict[str, Any]:
        res = {str(k): str(v) for k, v in list(data.items())}
        if "geneSetsTypes" in res:
            res["geneSetsTypes"] = ast.literal_eval(res["geneSetsTypes"])
        return res

    def get(self, request: Request) -> Response | StreamingHttpResponse:
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        data = self._parse_query_params(cast(dict, request.query_params))
        return self._build_response(data)


class GeneSetsHasDenovoView(QueryBaseView):
    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        if self.gpf_instance.denovo_gene_sets_db.has_gene_sets():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)
