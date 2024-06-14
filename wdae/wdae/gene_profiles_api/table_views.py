import logging

from datasets_api.permissions import get_instance_timestamp_etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from django.views.decorators.http import etag
from django.utils.decorators import method_decorator

LOGGER = logging.getLogger(__name__)


class TableConfigurationView(QueryBaseView):
    def get(self, _request):
        configuration = self.gpf_instance.get_wdae_gp_table_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(configuration)


class TableRowsView(QueryBaseView):
    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request):
        data = request.query_params
        page = int(data.get("page", 1))
        if page < 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        symbol_like = data.get("symbol", None)
        sort_by = data.get("sortBy", None)
        order = data.get("order", None)
        gps = self.gpf_instance.query_gp_statistics(
            page, symbol_like, sort_by, order)
        if gps is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(gps)


class GeneSymbolsView(QueryBaseView):
    """View for providing gene symbols."""
    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Get gene symbols from the gp table."""
        data = request.query_params
        page = int(data.get("page", 1))
        if page < 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        symbol_like = data.get("symbol", None)
        gps = self.gpf_instance.list_gp_gene_symbols(
            page, symbol_like)
        if gps is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(gps)
