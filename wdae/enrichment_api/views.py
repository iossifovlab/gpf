'''
Created on Feb 17, 2017

@author: lubo
'''
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import preloaded
import traceback
import precompute
from enrichment_tool.event_counters import EventsCounter, GeneEventsCounter
from common.query_base import GeneSymsMixin
from enrichment_api.enrichment_builder import EnrichmentBuilder


class EnrichmentModelsMixin(object):
    BACKGROUND_MODELS = [
        {
            'name': 'synonymousBackgroundModel',
            'desc':
            'Background model based on synonymous variants in transmitted'
        },
        {
            'name': 'codingLenBackgroundModel',
            'desc': 'Genes coding lenght background model'
        },
        {
            'name': 'samochaBackgroundModel',
            'desc': 'Background model described in Samocha et al',
        }
    ]

    COUNTING_MODELS = [
        {
            'name': 'enrichmentEventsCounting',
            'desc': 'Counting events'
        },
        {
            'name': 'enrichmentGeneCounting',
            'desc': 'Counting affected genes'
        },
    ]

    def get_default_background_name(self):
        config = settings.ENRICHMENT_CONFIG
        background_name = config['enrichmentBackgroundModel']
        return background_name

    def get_default_counting_name(self):
        config = settings.ENRICHMENT_CONFIG
        counting_name = config['enrichmentCountingModel']
        return counting_name

    def get_background_model(self, query):
        background_name = None
        if 'enrichmentModel' in query:
            enrichment_model = query['enrichmentModel']
            background_name = enrichment_model.get('background', None)
        if background_name is None:
            background_name = self.get_default_background_name()
        if precompute.register.has_key(background_name):  # @IgnorePep8
            background = precompute.register.get(background_name)
        else:
            background_name = self.get_default_background_name()
            background = precompute.register.get(background_name)
        return background

    def get_counting_model(self, query):
        counting_name = None
        if 'enrichmentModel' in query:
            enrichment_model = query['enrichmentModel']
            counting_name = enrichment_model.get('counting', None)
        if counting_name is None:
            counting_name = self.get_default_counting_name()

        if counting_name == 'enrichmentEventsCounting':
            counter_model = EventsCounter()
        elif counting_name == 'enrichmentGeneCounting':
            counter_model = GeneEventsCounter()
        else:
            raise KeyError('wrong denovo counter: {}'.format(counting_name))
        return counter_model

    def get_enrichment_model(self, data):
        return {
            'background': self.get_background_model(data),
            'counting': self.get_counting_model(data),
        }


class EnrichmentModelsView(APIView, EnrichmentModelsMixin):

    def get(self, request, enrichment_model_type):
        if enrichment_model_type == 'background':
            return Response(self.BACKGROUND_MODELS)
        if enrichment_model_type == 'counting':
            return Response(self.COUNTING_MODELS)

        return Response(status=status.HTTP_404_NOT_FOUND)


class EnrichmentTestView(APIView, EnrichmentModelsMixin):

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def enrichment_description(self, query):
        gene_sets_collection, gene_set, gene_sets_types = \
            GeneSymsMixin.get_gene_set_query(**query)
        if gene_set:
            if gene_sets_types:
                desc = "Gene Set: {} - {} ({})".format(
                    gene_sets_collection,
                    gene_set,
                    ','.join(gene_sets_types))
            else:
                desc = "Gene Set: {} - {}".format(
                    gene_sets_collection,
                    gene_set)
            return desc
        weights_id, range_start, range_end = \
            GeneSymsMixin.get_gene_weights_query(**query)
        if weights_id:
            if range_start and range_end:
                desc = "Gene Weights: {} from {} upto {}".format(
                    weights_id, range_start, range_end)
            elif range_start:
                desc = "Gene Weights: {} from {}".format(
                    weights_id, range_start)
            elif range_end:
                desc = "Gene Weights: {} upto {}".format(
                    weights_id, range_end)
            else:
                desc = "Gene Weights: {}".format(weights_id)
            return desc
        gene_syms = GeneSymsMixin.get_gene_symbols()
        if gene_syms:
            desc = "Gene Symbols: {}".format(gene_syms)
            return desc
        return None

    def post(self, request):
        query = request.data
        dataset_id = query.get('datasetId', None)
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset_desc = self.datasets_config.get_dataset_desc(dataset_id)
        if not dataset_desc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        dataset = self.datasets_factory.get_dataset(dataset_id)

        gene_syms = dataset.get_gene_syms(**query)
        print(gene_syms)
        if gene_syms is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        desc = self.enrichment_description(query)
        desc = "{} ({})".format(desc, len(gene_syms))
        try:
            enrichment_model = self.get_enrichment_model(query)
            builder = EnrichmentBuilder(
                dataset,
                enrichment_model,
                gene_syms)
            result = builder.build()
            result = builder.serialize()
            result['desc'] = desc
            result['children_stats'] = dataset.enrichment_children_stats
            result['selector_domain'] = dataset.enrichment_selector_domain()

            return Response(result)
        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
