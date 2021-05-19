import logging
from rest_framework import status
from rest_framework.response import Response

from dae.utils.helpers import to_response_json
from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    def get(self, request):
        configuration = self.gpf_instance.get_agp_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Camelize snake_cased keys, excluding "datasets"
        # since its keys are dataset IDs
        response = to_response_json(configuration)
        if "datasets" in configuration:
            response["datasets"] = dict()
            for dataset_id, conf in configuration["datasets"].items():
                response["datasets"][dataset_id] = to_response_json(conf)
                # Attach dataset display name to response
                dataset_conf = self.gpf_instance.get_genotype_data_config(
                    dataset_id
                )
                conf["name"] = dataset_conf.get("name", dataset_id)

        return Response(response)


class ProfileView(QueryBaseView):
    def get(self, request, gene_symbol):
        agp = self.gpf_instance.get_agp_statistic(gene_symbol)
        if not agp:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(agp.to_json())


class QueryProfilesView(QueryBaseView):
    def get(self, request):
        data = request.query_params
        page = int(data.get("page", 1))
        if page < 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        symbol_like = data.get("symbol", None)
        sort_by = data.get("sortBy", None)
        order = data.get("order", None)

        agps = self.gpf_instance.query_agp_statistics(
            page, symbol_like, sort_by, order)

        if agps is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response([agp.to_json() for agp in agps])
