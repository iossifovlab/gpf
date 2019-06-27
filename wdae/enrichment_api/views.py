'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import logging
import traceback

from common.query_base import GeneSymsMixin

from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_api.enrichment_serializer import EnrichmentSerializer

from users_api.authentication import SessionAuthenticationWithoutCSRF

from gene_sets.expand_gene_set_decorator import expand_gene_set

from datasets_api.studies_manager import get_studies_manager

# from memory_profiler import profile
# fp = open('memory_profiler_basic_mean.log', 'w+')
# precision = 5

LOGGER = logging.getLogger(__name__)


class EnrichmentModelsView(APIView):

    def __init__(self):
        self.enrichment_facade = get_studies_manager().get_enrichment_facade()

    def get_from_config(self, dataset_id, key):
        enrichment_config = \
            self.enrichment_facade.get_all_study_enrichment_configs(dataset_id)

        if enrichment_config is None:
            return []

        return [
            {
                'name': el['name'],
                'desc': el['desc']
            } for el in enrichment_config[key].values()
        ]

    def get(self, request, dataset_id=None):
        result = {
            'background': self.get_from_config(dataset_id, 'backgrounds'),
            'counting': self.get_from_config(dataset_id, 'counting'),
        }
        return Response(result)


class EnrichmentTestView(APIView):

    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        self.variants_db = get_studies_manager().get_variants_db()
        self.enrichment_facade = get_studies_manager().get_enrichment_facade()

        self.gene_info_config = get_studies_manager().get_gene_info_config()

    def enrichment_description(self, query):
        gene_set = query.get('geneSet')
        if gene_set:
            desc = 'Gene Set: {}'.format(gene_set)
            return desc

        weights_id, range_start, range_end = \
            GeneSymsMixin.get_gene_weights_query(
                self.gene_info_config, **query)
        if weights_id:
            if range_start and range_end:
                desc = 'Gene Weights: {} from {} upto {}'.format(
                    weights_id, range_start, range_end)
            elif range_start:
                desc = 'Gene Weights: {} from {}'.format(
                    weights_id, range_start)
            elif range_end:
                desc = 'Gene Weights: {} upto {}'.format(weights_id, range_end)
            else:
                desc = 'Gene Weights: {}'.format(weights_id)
            return desc

        gene_syms = GeneSymsMixin.get_gene_symbols(**query)
        if gene_syms:
            desc = 'Gene Symbols: {}'.format(','.join(gene_syms))
            return desc

        return None

    @expand_gene_set
    def post(self, request):
        query = request.data

        dataset_id = query.get('datasetId', None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        background_name = query.get('enrichmentBackgroundModel', None)
        counting_name = query.get('enrichmentCountingModel', None)

        dataset = self.variants_db.get(dataset_id)
        if not dataset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        gene_syms = GeneSymsMixin.get_gene_syms(self.gene_info_config, **query)
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        desc = self.enrichment_description(query)
        desc = '{} ({})'.format(desc, len(gene_syms))
        try:
            enrichment_tool = self.enrichment_facade.get_enrichment_tool(
                dataset_id, background_name, counting_name)
            enrichment_config = enrichment_tool.config

            if enrichment_tool.background is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            builder = EnrichmentBuilder(dataset, enrichment_tool, gene_syms)
            results = builder.build()

            serializer = EnrichmentSerializer(enrichment_config, results)
            results = serializer.serialize()

            enrichment = {
                'desc': desc,
                'result': results
            }
            return Response(enrichment)
        except Exception:
            LOGGER.exception('error while processing genotype query')
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
