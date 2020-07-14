from rest_framework.response import Response
from rest_framework import status

import logging

from .enrichment_builder import EnrichmentBuilder
from .enrichment_serializer import EnrichmentSerializer

from query_base.query_base import QueryBaseView

from dae.utils.gene_utils import GeneSymsMixin

from gene_sets.expand_gene_set_decorator import expand_gene_set

from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import CounterBase

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
        # FIXME: Rewrite this when returning to box
        if isinstance(enrichment_config, dict):
            selected_properties = enrichment_config[selected]
            result = []
            for prop_name in selected_properties:
                prop = enrichment_config[property_name][prop_name]
                result.append(prop)
            return result
        else:
            selected_properties = getattr(enrichment_config, selected)
            return [
                {"name": el.name, "desc": el.desc}
                for el in getattr(enrichment_config, property_name)
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
            weights_id,
            range_start,
            range_end,
        ) = GeneSymsMixin.get_gene_weights_query(
            self.gene_info_config.gene_weights, **query
        )
        if weights_id:
            if range_start and range_end:
                desc = "Gene Weights: {} from {} upto {}".format(
                    weights_id, range_start, range_end
                )
            elif range_start:
                desc = "Gene Weights: {} from {}".format(
                    weights_id, range_start
                )
            elif range_end:
                desc = "Gene Weights: {} upto {}".format(weights_id, range_end)
            else:
                desc = "Gene Weights: {}".format(weights_id)
            return desc

        gene_syms = GeneSymsMixin.get_gene_symbols(**query)
        if gene_syms:
            desc = "Gene Symbols: {}".format(",".join(gene_syms))
            return desc

        return None

    def get_enrichment_tool(self, enrichment_config, query):
        dataset_id = query.get("datasetId", None)

        background_name = query.get("enrichmentBackgroundModel", None)

        if (
            background_name is None
            or not self.gpf_instance.has_background(
                dataset_id, background_name
            )
        ):
            background_name = enrichment_config.default_background_model
        counting_name = query.get(
            "enrichmentCountingModel",
            enrichment_config.default_counting_model,
        )

        background = self.gpf_instance.get_study_background(
            dataset_id, background_name
        )
        counter = CounterBase.counters()[counting_name]()
        enrichment_tool = EnrichmentTool(
            enrichment_config, background, counter
        )

        return enrichment_tool

    @expand_gene_set
    def post(self, request):
        query = request.data

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_dataset(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        enrichment_config = self.gpf_instance.get_study_enrichment_config(
            dataset_id
        )
        enrichment_tool = self.get_enrichment_tool(enrichment_config, query)

        gene_syms = GeneSymsMixin.get_gene_syms(
            self.gpf_instance.get_gene_info_gene_weights(), **query
        )
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        desc = self.enrichment_description(query)
        desc = "{} ({})".format(desc, len(gene_syms))

        if enrichment_tool.background is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        builder = EnrichmentBuilder(dataset, enrichment_tool, gene_syms)
        results = builder.build()

        serializer = EnrichmentSerializer(enrichment_config, results)
        results = serializer.serialize()

        enrichment = {"desc": desc, "result": results}
        return Response(enrichment)
