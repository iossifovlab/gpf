import logging

from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


class TableRowsView(QueryBaseView):
    """View for providing pages of gene profiles table statistic rows"""
    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """"Get gene profiles table statistics row page"""
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
