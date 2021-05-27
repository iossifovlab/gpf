import logging
from rest_framework import status
from rest_framework.response import Response

from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    def get(self, request):
        configuration = self.gpf_instance.get_agp_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Attach dataset display name to configuration
        if "datasets" in configuration:
            for dataset_id, dataset in configuration["datasets"].items():
                study_wrapper = self.gpf_instance.get_wdae_wrapper(dataset_id)
                dataset["name"] = study_wrapper.config.get("name", dataset_id)

                if "person_sets" in dataset:
                    # De-box and attach person set counts
                    dataset["person_sets"] = list(map(
                        lambda ps: ps.to_dict(), dataset["person_sets"]
                    ))
                    for person_set in dataset["person_sets"]:
                        set_id = person_set['set_name']
                        collection_id = person_set['collection_name']
                        person_set_collection = \
                            study_wrapper.genotype_data.person_set_collections[
                                collection_id
                            ]
                        stats = person_set_collection.get_stats()[set_id]
                        person_set['parents_count'] = stats['parents']
                        person_set['children_count'] = stats['children']

        return Response(configuration)


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
