from django.http.response import StreamingHttpResponse, FileResponse

from rest_framework import status  # type: ignore
from rest_framework.response import Response  # type: ignore

import json
import logging
import itertools

from utils.logger import LOGGER
from utils.streaming_response_util import iterator_to_json
from utils.logger import request_logging

from query_base.query_base import QueryBaseView

from gene_sets.expand_gene_set_decorator import expand_gene_set

from studies.study_wrapper import StudyWrapperBase

from datasets_api.permissions import handle_partial_permissions, \
    user_has_permission
from dae.utils.dae_utils import join_line


logger = logging.getLogger(__name__)


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
        user = request.user

        if "queryData" in data:
            data = self._parse_query_params(data)
        dataset_id = data.pop("datasetId", None)

        if not user_has_permission(request.user, dataset_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if "genomicScores" in data:
            scores = data["genomicScores"]
            for score in scores:
                if score["rangeStart"] is None and score["rangeEnd"] is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        is_download = data.pop("download", False)

        if "maxVariantsCount" in data:
            max_variants = data["maxVariantsCount"]
        else:
            if is_download:
                max_variants = 10000
                if not user.is_anonymous and \
                        (user.is_staff or user.has_unlimitted_download):
                    max_variants = None
            else:
                max_variants = self.MAX_SHOWN_VARIANTS + 1

        if max_variants == -1:
            # unlimitted variants preview
            max_variants = None

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if "sources" in data:
            sources = data.pop("sources")
        else:
            # TODO Handle summary variant preview and download sources
            if is_download:
                cols = dataset.config.genotype_browser.download_columns
            else:
                cols = dataset.config.genotype_browser.preview_columns
            sources = StudyWrapperBase.get_columns_as_sources(
                dataset.config, cols
            )

        handle_partial_permissions(user, dataset_id, data)

        if is_download:
            response = dataset.query_variants_wdae(
                data, sources,
                max_variants_count=max_variants,
                max_variants_message=is_download
            )
            columns = [s.get("name", s["source"]) for s in sources]
            response = map(
                join_line, itertools.chain([columns], response))
            response = FileResponse(
                response, filename='variants.tsv',
                as_attachment=True, content_type="text/tsv"
            )
            response["Content-Disposition"] = \
                "attachment; filename=variants.tsv"
            response["Expires"] = "0"
        else:
            response = dataset.query_variants_wdae_streaming(
                data, sources,
                max_variants_count=max_variants,
                max_variants_message=is_download
            )
            response = StreamingHttpResponse(
                iterator_to_json(response),
                status=status.HTTP_200_OK,
                content_type="text/event-stream",
            )

        response["Cache-Control"] = "no-cache"
        return response
