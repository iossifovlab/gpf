import logging
from rest_framework import status
from rest_framework.response import Response

from dae.utils.helpers import to_response_json
from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


class ConfigurationView(QueryBaseView):
    def find_category_section(self, configuration, category):
        for gene_set in configuration["geneSets"]:
            if gene_set["category"] == category:
                return "geneSets"
        for genomic_score in configuration["genomicScores"]:
            if genomic_score["category"] == category:
                return "genomicScores"
        for dataset in configuration["datasets"]:
            if dataset["id"] == category:
                return "datasets"

    def get(self, request):
        configuration = self.gpf_instance.get_agp_configuration()
        if configuration is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = {"config": []}
        if len(configuration) == 0:
            return Response(response)

        response["config"].append({
            "id": "geneSymbol",
            "displayName": "Gene",
            "visible": True,
            "columns": []
        })

        for category in configuration["gene_sets"]:
            response["config"].append({
                "id": category["category"],
                "displayName": category["display_name"],
                "visible": True,
                "columns": [{
                    "id": gene_set["set_id"],
                    "displayName": gene_set["set_id"],
                    "visible": True,
                    "columns": []
                } for gene_set in category["sets"]]
            })

        for category in configuration["genomic_scores"]:
            response["config"].append({
                "id": category["category"],
                "displayName": category["display_name"],
                "visible": True,
                "columns": [{
                    "id": genomic_score["score_name"],
                    "displayName": genomic_score["score_name"],
                    "visible": True,
                    "columns": []
                } for genomic_score in category["scores"]]
            })

        if "datasets" in configuration:
            all_datasets_col = {
                "id": "datasets",
                "displayName": "Datasets",
                "visible": True,
                "columns": list()
            }
            for dataset_id, dataset in configuration["datasets"].items():
                study_wrapper = self.gpf_instance.get_wdae_wrapper(dataset_id)
                display_name = dataset.get("display_name") \
                    or study_wrapper.config.get("name") \
                    or dataset_id
                dataset_col = {
                    "id": dataset_id,
                    "displayName": display_name,
                    "visible": True,
                    "columns": list()
                }
                for person_set in dataset.get("person_sets", []):
                    set_id = person_set["set_name"]
                    collection_id = person_set["collection_name"]
                    person_set_collection = \
                        study_wrapper.genotype_data.person_set_collections[
                            collection_id
                        ]
                    set_name = \
                        person_set_collection.person_sets[set_id].name
                    dataset_col["columns"].append({
                        "id": set_id,
                        "displayName": set_name,
                        "visible": True,
                        "columns": [
                            { "id": statistic.id,
                              "displayName": statistic.display_name,
                              "visible": True,
                              "columns": list() }
                            for statistic in dataset["statistics"]
                        ]
                    })
                all_datasets_col["columns"].append(dataset_col)
            response["config"].append(all_datasets_col)

        return Response(response)


class ProfileView(QueryBaseView):
    def get(self, request, gene_symbol):
        agp = self.gpf_instance.get_agp_statistic(gene_symbol)
        if not agp:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(agp)


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
        return Response(agps)
