from django.http.response import StreamingHttpResponse, FileResponse, HttpResponse

from rest_framework import status
from rest_framework.response import Response

import json
import logging
import itertools

from utils.logger import LOGGER
from utils.streaming_response_util import iterator_to_json
from utils.logger import request_logging

from query_base.query_base import QueryBaseView

from gene_sets.expand_gene_set_decorator import expand_gene_set

from datasets_api.permissions import \
    get_allowed_genotype_studies

from dae.utils.dae_utils import join_line


logger = logging.getLogger(__name__)


def handle_partial_permissions(user, dataset_id: str, request_data: dict):
    """A user may have only partial access to a dataset based
    on which of its constituent studies he has rights to access.
    This method attaches these rights to the request as study filters
    in order to filter variants from studies the user cannot access.
    """

    request_data["allowed_studies"] = \
        get_allowed_genotype_studies(user, dataset_id)


class GenotypeBrowserQueryView(QueryBaseView):

    MAX_SHOWN_VARIANTS = 1000

    def _parse_query_params(self, data):
        res = {str(k): str(v) for k, v in list(data.items())}
        assert "queryData" in res
        query = json.loads(res["queryData"])
        return query

    @expand_gene_set
    @request_logging(LOGGER)
    def post(self, request):
        LOGGER.info("query v3 variants request: " + str(request.data))

        data = request.data
        if "queryData" in data:
            data = self._parse_query_params(data)
        dataset_id = data.pop("datasetId", None)

        if "sources" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if "genomicScores" in data:
            scores = data["genomicScores"]
            for score in scores:
                if score["rangeStart"] is None and score["rangeEnd"] is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        sources = data.pop("sources")

        is_download = data.pop("download", False)

        max_variants = data.pop(
            "maxVariantsCount", self.MAX_SHOWN_VARIANTS + 1)
        if max_variants == -1:
            # unlimitted variants preview
            max_variants = None

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        user = request.user

        handle_partial_permissions(user, dataset_id, data)

        response = dataset.query_variants_wdae(
            data, sources, max_variants_count=max_variants
        )

        if is_download:
            columns = [s.get("name", s["source"]) for s in sources]
            response = map(
                join_line, itertools.chain([columns], response))
            response = FileResponse(
                response, filename='variants.tsv',
                as_attachment=True, content_type="text/tsv"
            )
        else:
            response = StreamingHttpResponse(
                iterator_to_json(response),
                status=status.HTTP_200_OK,
                content_type="text/event-stream",
            )

        response["Cache-Control"] = "no-cache"
        return response
