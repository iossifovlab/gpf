import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from query_base.query_base import QueryBaseView


logger = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    def get(self, _request: Request) -> Response:
        configuration = self.gpf_instance.get_wdae_agp_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(configuration)


class ProfileView(QueryBaseView):
    def get(self, _request: Request, gene_symbol: str) -> Response:
        agp = self.gpf_instance.get_agp_statistic(gene_symbol)
        if not agp:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(agp.to_json())
