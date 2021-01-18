import logging
import json
from rest_framework import status
from rest_framework.response import Response

from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    def get(self, request):
        configuration = self.gpf_instance.get_agp_configuration()
        if not configuration:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(configuration)


class ProfileView(QueryBaseView):
    def get(self, request, gene_symbol):
        agp = self.gpf_instance.get_agp_statistic(gene_symbol)
        if not agp:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(agp.to_json())


class QueryProfilesView(QueryBaseView):
    def get(self, request):
        agps = self.gpf_instance.get_all_agp_statistics()
        if not agps:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response([agp.to_json() for agp in agps])
