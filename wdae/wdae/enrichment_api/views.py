from rest_framework.response import Response
from rest_framework import status

import logging

from query_base.query_base import QueryBaseView

from dae.utils.gene_utils import GeneSymsMixin

from gene_sets.expand_gene_set_decorator import expand_gene_set


# from memory_profiler import profile
# fp = open('memory_profiler_basic_mean.log', 'w+')
# precision = 5

LOGGER = logging.getLogger(__name__)


class EnrichmentModelsView(QueryBaseView):
    def __init__(self):
        super(EnrichmentModelsView, self).__init__()

    def get_from_config(self, dataset_id, property_name, selected):
        enrichment_config = self.gpf_instance.get_study_enrichment_config(
            dataset_id
        )
        if enrichment_config is None:
            return []

        selected_properties = enrichment_config[selected]

        return [
            {"name": el.name, "desc": el.desc}
            for el in enrichment_config[property_name].values()
            if el.name in selected_properties
        ]

    def get(self, request, dataset_id=None):
        result = {
            "background": self.get_from_config(
                dataset_id, "background", "selected_background_values"
            ),
            "counting": self.get_from_config(
                dataset_id, "counting", "selected_counting_values"
            ),
        }
        return Response(result)


class EnrichmentTestView(QueryBaseView):
    def __init__(self):
        super(EnrichmentTestView, self).__init__()

        self.gene_info_config = self.gpf_instance._gene_info_config

    def enrichment_description(self, query):
        gene_set = query.get("geneSet")
        if gene_set:
            desc = "Gene Set: {}".format(gene_set)
            return desc

        (
            gene_scores_id,
            range_start,
            range_end,
        ) = GeneSymsMixin.get_gene_scores_query(
            self.gene_info_config.gene_weights, **query
        )
        if gene_scores_id:
            if range_start and range_end:
                desc = "Gene Scores: {} from {} upto {}".format(
                    gene_scores_id, range_start, range_end
                )
            elif range_start:
                desc = "Gene Scores: {} from {}".format(
                    gene_scores_id, range_start
                )
            elif range_end:
                desc = "Gene Scores: {} upto {}".format(gene_scores_id, range_end)
            else:
                desc = "Gene Scores: {}".format(gene_scores_id)
            return desc

        gene_syms = GeneSymsMixin.get_gene_symbols(**query)
        if gene_syms:
            desc = "Gene Symbols: {}".format(",".join(gene_syms))
            return desc

        return None

    @expand_gene_set
    def post(self, request):
        query = request.data

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = GeneSymsMixin.get_gene_syms(
            self.gpf_instance.get_gene_info_gene_weights(), **query
        )
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        desc = self.enrichment_description(query)
        desc = "{} ({})".format(desc, len(gene_syms))

        background_name = query.get("enrichmentBackgroundModel", None)
        counting_name = query.get("enrichmentCountingModel", None)

        builder = self.gpf_instance.create_enrichment_builder(
            dataset_id, background_name, counting_name, gene_syms)

        if builder is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results = builder.build()

        enrichment = {"desc": desc, "result": results}
        return Response(enrichment)
