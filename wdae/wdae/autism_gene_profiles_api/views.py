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

        # Camelize snake_cased keys, excluding "datasets"
        # since its keys are dataset IDs
        response = to_response_json(configuration)
        if len(configuration) == 0:
            return Response(response)

        if "datasets" in configuration:
            response["datasets"] = list()
            for dataset_id, dataset in configuration["datasets"].items():
                study_wrapper = self.gpf_instance.get_wdae_wrapper(dataset_id)

                if "person_sets" in dataset:
                    # Attach person set counts
                    person_sets_config = list()
                    for person_set in dataset["person_sets"]:
                        set_id = person_set["set_name"]
                        collection_id = person_set["collection_name"]
                        description = ""
                        if "description" in person_set:
                            description = person_set["description"]
                        person_set_collection = \
                            study_wrapper.genotype_data.person_set_collections[
                                collection_id
                            ]
                        stats = person_set_collection.get_stats()[set_id]
                        set_name = \
                            person_set_collection.person_sets[set_id].name
                        person_sets_config.append({
                            "id": set_id,
                            "displayName": set_name,
                            "collectionId": collection_id,
                            "description": description,
                            "parentsCount": stats["parents"],
                            "childrenCount": stats["children"],
                            "statistics": to_response_json(dataset)["statistics"],
                        })

                display_name = dataset.get("display_name")
                if display_name is None:
                    display_name = study_wrapper.config.get("name")
                if display_name is None:
                    display_name = dataset_id

                response["datasets"].append({
                    "id": dataset_id,
                    "displayName": display_name,
                    "defaultVisible": True,
                    **to_response_json(dataset),
                    "personSets": person_sets_config,  # overwrite person_sets
                })

        assert "order" in response

        order = response["order"]
        response["order"] = [
            {"section": self.find_category_section(response, o), "id": o}
            for o in order
        ]

        return Response(response)


class ProfileView(QueryBaseView):
    def get(self, request, gene_symbol):
        agp = self.gpf_instance.get_agp_statistic(gene_symbol)
        if not agp:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(agp.to_json())