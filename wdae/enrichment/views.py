'''
Created on Jun 12, 2015

@author: lubo
'''
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from helpers.wdae_query_variants import combine_gene_syms, gene_set_loader2
from enrichment.config import PHENOTYPES, EFFECT_TYPES
from enrichment.counters import EventsCounter, \
    GeneEventsCounter
from enrichment.families import ChildrenStats
# from enrichment.results import EnrichmentTestBuilder
from helpers.logger import LOGGER, log_filter
from helpers.pvalue import colormap_value
from precompute import register
from query_prepare import prepare_denovo_studies, \
    prepare_string_value
from rest_framework import status
from helpers.dae_query import prepare_query_dict
from enrichment.counters import DenovoStudies
from enrichment.enrichment_builder import EnrichmentBuilder, RowResult

# from helpers.profiler import profile


class EnrichmentModelsView(APIView):

    BACKGROUND_MODELS = [
        {'name': 'synonymousBackgroundModel',
         'desc':
         'Background model based on synonymous variants in transmitted'},
        {'name': 'codingLenBackgroundModel',
         'desc': 'Genes coding lenght background model'},
        {'name': 'samochaBackgroundModel',
         'desc': 'Background model described in Samocha et al',
         }
    ]

    COUNTING_MODELS = [
        {'name': 'enrichmentEventsCounting',
         'desc': 'Counting events'},
        {'name': 'enrichmentGeneCounting',
         'desc': 'Counting affected genes'},
    ]

    def get(self, request, enrichment_model_type):
        if enrichment_model_type == 'background':
            return Response(self.BACKGROUND_MODELS)
        if enrichment_model_type == 'counting':
            return Response(self.COUNTING_MODELS)

        return Response(status=status.HTTP_404_NOT_FOUND)


class EnrichmentView(APIView):

    def __init__(self):
        self.data = {}

    @staticmethod
    def enrichment_prepare(data):
        if data['denovoStudies']:
            del data['denovoStudies']
        data['denovoStudies'] = 'ALL WHOLE EXOME'

        result = {
            'denovoStudies': prepare_denovo_studies(data),
            'geneSet': prepare_string_value(data, 'geneSet'),
            'geneTerm': prepare_string_value(data, 'geneTerm'),
            'gene_set_phenotype':
            prepare_string_value(data, 'gene_set_phenotype'),
            'geneSyms': combine_gene_syms(data),
            'geneWeight': prepare_string_value(data, 'geneWeight'),
            'geneWeightMin': prepare_string_value(data, 'geneWeightMin'),
            'geneWeightMax': prepare_string_value(data, 'geneWeightMax'),
        }

        if 'geneSet' not in result or result['geneSet'] is None or \
           'geneTerm' not in result or result['geneTerm'] is None:

            del result['geneSet']
            del result['geneTerm']
            del result['gene_set_phenotype']

        if 'geneSet' in result and result['geneSet'] != 'denovo':
            del result['gene_set_phenotype']

        if 'geneWeight' not in result or result['geneWeight'] is None or \
                'geneWeightMin' not in result or \
                result['geneWeightMin'] is None or \
                'geneWeightMax' not in result or \
                result['geneWeightMax'] is None:

            del result['geneWeight']
            del result['geneWeightMin']
            del result['geneWeightMax']

        if not all(result.values()):
            return None

        dsts = result['denovoStudies']
        result['denovoStudies'] = [
            st for st in dsts
            if st.get_attr('study.type') == 'WE']

        return result

    def serialize_response_common_data(self):
        res = {}
        res['gs_id'] = self.gene_set

        if self.gene_set is None:
            gene_terms = None
        else:
            gene_terms = gene_set_loader2(
                self.gene_set, self.gene_set_phenotype)

        if self.gene_set and self.gene_term and gene_terms:
            res['gs_desc'] = "Gene Set: %s: %s" % \
                (self.gene_term,
                 gene_terms.tDesc[self.gene_term])
        elif self.gene_weight is not None and \
                self.gene_weight_min is not None and \
                self.gene_weight_max is not None:

            res['gs_desc'] = "Gene Weights: %s: from %s to %s" % \
                (self.gene_weight,
                 self.gene_weight_min,
                 self.gene_weight_max)
        else:
            syms = list(self.gene_syms)
            desc = ','.join(sorted(syms))
            res['gs_desc'] = desc
            res['gs_id'] = desc

        res['gene_number'] = len(self.gene_syms)
        res['phenotypes'] = PHENOTYPES
        return res

#     def serialize_response_test(self, t):
#         print(t)
#         tres = {}
#         tres['overlap'] = t.total
#         tres['count'] = t.count
#
#         tres['label'] = t.name
#         if t.type == 'rec':
#             tres['syms'] = t.gene_syms.intersection(self.gene_syms)
#         tres['filter'] = t.filter
#
#         if t.p_val >= 0.0001:
#             tres['p_val'] = round(t.p_val, 4)
#         else:
#             tres['p_val'] = str('%.1E' % t.p_val)
#
#         tres['expected'] = round(t.expected, 4)
#
#         if t.count > t.expected:
#             lessmore = 'more'
#         elif t.count < t.expected:
#             lessmore = 'less'
#         else:
#             lessmore = 'equal'
#
#         tres['lessmore'] = lessmore
#         tres['bg'] = colormap_value(t.p_val, lessmore)
#         return tres

    def serialize_response_test(self, t):
        def less_more(count, expected):
            lessmore = 'more'
            if count > expected:
                lessmore = 'more'
            elif count < expected:
                lessmore = 'less'
            else:
                lessmore = 'equal'
            return lessmore

        tres = {}
        tres['overlap'] = t.count
        tres['count'] = t.overlapped_count

        tres['label'] = t.name
        if t.rec:
            tres['syms'] = t.overlapped_gene_syms
        tres['filter'] = t.filter

        if t.pvalue >= 0.0001:
            tres['p_val'] = round(t.pvalue, 4)
        else:
            tres['p_val'] = str('%.1E' % t.pvalue)

        tres['expected'] = round(t.expected, 4)

        lessmore = less_more(t.overlapped_count, t.expected)

        tres['lessmore'] = lessmore
        tres['bg'] = colormap_value(t.pvalue, lessmore)
        return tres

    def serialize_response_results(self):
        result = {}
        for phenotype in PHENOTYPES:
            res = []
            for effect_type in EFFECT_TYPES:
                for test_type in RowResult.TESTS:
                    t = self.result[phenotype][effect_type][test_type]
                    tres = self.serialize_response_test(t)
                    res.append(tres)
            result[phenotype] = res
        return result

#         for phenotype, tests in self.result.items():
#             res = []
#             for t in tests:
#                 tres = self.serialize_response_test(t)
#                 res.append(tres)
#             result[phenotype] = res
#         return result

    def serialize(self):
        res1 = self.serialize_response_common_data()
        res2 = self.serialize_response_results()
        res1.update(res2)
        return res1

    @property
    def gene_set(self):
        return self.data.get('geneSet', None)

    @property
    def gene_term(self):
        return self.data.get('geneTerm', None)

    @property
    def gene_set_phenotype(self):
        return self.data.get('gene_set_phenotype', None)

    @property
    def gene_syms(self):
        return self.data.get('geneSyms', None)

    @property
    def gene_weight(self):
        return self.data.get('geneWeight', None)

    @property
    def gene_weight_min(self):
        return self.data.get('geneWeightMin', None)

    @property
    def gene_weight_max(self):
        return self.data.get('geneWeightMax', None)

    @property
    def denovo_studies(self):
        return self.data.get('denovoStudies', None)

    def background_config(self, data):
        background_model = prepare_string_value(
            data, 'enrichmentBackgroundModel')
        if background_model is None:
            config = settings.ENRICHMENT_CONFIG
            background_model = config['enrichmentBackgroundModel']

        if register.has_key(background_model):  # @IgnorePep8
            background = register.get(background_model)
        else:
            background = register.get('synonymousBackgroundModel')
        return background

    def counting_config(self, data):
        counting_model = prepare_string_value(
            data, 'enrichmentCountingModel')
        if counting_model is None:
            config = settings.ENRICHMENT_CONFIG
            counting_model = config['enrichmentCountingModel']

        if counting_model == 'enrichmentEventsCounting':
            counter_cls = EventsCounter
        elif counting_model == 'enrichmentGeneCounting':
            counter_cls = GeneEventsCounter
        else:
            raise KeyError('wrong denovo counter: {}'.format(counting_model))

        return counter_cls

    def enrichment_config(self, data):
        return {
            'background': self.background_config(data),
            'denovo_counter': self.counting_config(data),
        }

    # @profile("enrichment_get.prof")
    def get(self, request):
        query_data = prepare_query_dict(request.query_params)
        LOGGER.info(log_filter(
            request,
            "enrichment query by phenotype: %s" % str(query_data)))

        self.data = self.enrichment_prepare(query_data)

        if self.data is None:
            return Response(None)

        config = self.enrichment_config(query_data)
        denovo_studies = DenovoStudies()
        children_stats = ChildrenStats.build(denovo_studies)
        print(children_stats)

        self.enrichment = EnrichmentBuilder(
            config['background'], config['denovo_counter'],
            denovo_studies, self.gene_syms,
            children_stats)
        self.result = self.enrichment.build()

        response = self.serialize()
        response['children_stats'] = children_stats

        return Response(response)
