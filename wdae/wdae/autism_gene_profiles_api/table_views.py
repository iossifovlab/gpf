import logging
from rest_framework import status
from rest_framework.response import Response

from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


def column(
    id, display_name, visible=True, clickable=None,
    display_vertical=False, sortable=False, columns=None, meta=None):
    if columns is None:
        columns = list()
    return {
        "id": id,
        "displayName": display_name,
        "visible": visible,
        "displayVertical": display_vertical,
        "sortable": sortable,
        "clickable": clickable,
        "columns": columns,
        "meta": meta
    }


class TableConfigurationView(QueryBaseView):
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

        if len(configuration) == 0:
            return Response(dict())

        response = {
            "defaultDataset": configuration.get("default_dataset"),
            "columns": [],
            "pageSize": self.gpf_instance._autism_gene_profile_db.PAGE_SIZE,
        }

        response["columns"].append(
            column("geneSymbol", "Gene", clickable="createTab")
        )

        for category in configuration["gene_sets"]:
            response["columns"].append(column(
                f"{category['category']}_rank",
                category["display_name"],
                visible=category.get("default_visible", True),
                meta=category.get("meta"),
                sortable=True,
                columns=[column(
                    f"{category['category']}_rank.{gene_set['set_id']}",
                    gene_set["set_id"],
                    visible=gene_set.get("default_visible", True),
                    meta=gene_set.get("meta"),
                    display_vertical=True,
                    sortable=True) for gene_set in category["sets"]
                ]
            ))

        for category in configuration["genomic_scores"]:
            response["columns"].append(column(
                category["category"],
                category["display_name"],
                visible=category.get("default_visible", True),
                meta=category.get("meta"),
                columns=[column(
                    f"{category['category']}.{genomic_score['score_name']}",
                    genomic_score["score_name"],
                    visible=genomic_score.get("default_visible", True),
                    meta=genomic_score.get("meta"),
                    display_vertical=True,
                    sortable=True) for genomic_score in category["scores"]
                ]
            ))

        if "datasets" in configuration:
            for dataset_id, dataset in configuration["datasets"].items():
                study_wrapper = self.gpf_instance.get_wdae_wrapper(dataset_id)
                display_name = dataset.get("display_name") \
                    or study_wrapper.config.get("name") \
                    or dataset_id
                dataset_col = column(
                    f"{dataset_id}", display_name,
                    visible=dataset.get("default_visible", True),
                    meta=dataset.get("meta"),
                )
                for person_set in dataset.get("person_sets", []):
                    set_id = person_set["set_name"]
                    collection_id = person_set["collection_name"]
                    person_set_collection = \
                        study_wrapper.genotype_data.person_set_collections[
                            collection_id
                        ]
                    set_name = \
                        person_set_collection.person_sets[set_id].name
                    stats = person_set_collection.get_stats()[set_id]
                    dataset_col["columns"].append(column(
                        f"{dataset_id}.{set_id}",
                        f"{set_name} ({stats['children']})",
                        visible=person_set.get("default_visible", True),
                        meta=person_set.get("meta"),
                        columns=[column(
                            f"{dataset_id}.{set_id}.{statistic.id}",
                            statistic.display_name,
                            visible=statistic.get("default_visible", True),
                            meta=statistic.get("meta"),
                            clickable="goToQuery",
                            sortable=True)

                            for statistic in dataset["statistics"]
                        ]
                    ))
                response["columns"].append(dataset_col)

        if configuration.get("order"):
            category_order = ["geneSymbol", *configuration["order"]]
            response["columns"].sort(key=lambda col: category_order.index(col['id']))

        return Response(response)


class TableRowsView(QueryBaseView):
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
