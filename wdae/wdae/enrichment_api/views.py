from rest_framework.response import Response
from rest_framework import status

import logging

from query_base.query_base import QueryBaseView

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

        self.gene_scores_db = self.gpf_instance.gene_scores_db

    def _parse_gene_syms(self, query):
        gene_syms = query.get("geneSymbols", None)
        if gene_syms is None:
            gene_syms = set([])
        else:
            if isinstance(gene_syms, str):
                gene_syms = gene_syms.split(",")
            gene_syms = set([g.strip() for g in gene_syms])
        return gene_syms

    def enrichment_description(self, query):
        gene_set = query.get("geneSet")
        if gene_set:
            desc = "Gene Set: {}".format(gene_set)
            return desc

        gene_score_request = query.get("geneScores", None)
        gene_scores_id = None
        if gene_score_request is not None:
            gene_scores_id = gene_score_request.get("score", None)
            range_start = gene_score_request.get("rangeStart", None)
            range_end = gene_score_request.get("rangeEnd", None)
        if gene_scores_id is not None and \
                gene_scores_id in self.gene_scores_db:
            if range_start and range_end:
                desc = "Gene Scores: {} from {} upto {}".format(
                    gene_scores_id, range_start, range_end
                )
            elif range_start:
                desc = "Gene Scores: {} from {}".format(
                    gene_scores_id, range_start
                )
            elif range_end:
                desc = "Gene Scores: {} upto {}".format(
                    gene_scores_id, range_end
                )
            else:
                desc = "Gene Scores: {}".format(gene_scores_id)
            return desc

        gene_syms = self._parse_gene_syms(query)

        desc = "Gene Symbols: {}".format(",".join(gene_syms))
        return desc

    @expand_gene_set
    def post(self, request):
        query = request.data

        dataset_id = query.get("datasetId", None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = None
        if "geneSymbols" in query:
            gene_syms = self._parse_gene_syms(query)
        else:
            gene_score_request = query.get("geneScores", None)
            if gene_score_request is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            gene_score_id = gene_score_request.get("score", None)
            range_start = gene_score_request.get("rangeStart", None)
            range_end = gene_score_request.get("rangeEnd", None)

            if gene_score_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if gene_score_id in self.gene_scores_db:
                gene_score = self.gene_scores_db.get_gene_score(
                    gene_score_id
                )
                gene_syms = gene_score.get_genes(
                    wmin=range_start,
                    wmax=range_end
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
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
