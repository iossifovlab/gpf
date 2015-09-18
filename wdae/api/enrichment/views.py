'''
Created on Jun 12, 2015

@author: lubo
'''
from rest_framework.views import APIView
from api.query.query_prepare import prepare_denovo_studies, \
    prepare_string_value, \
    combine_gene_syms
from api.views import prepare_query_dict, log_filter
from rest_framework.response import Response
from api.logger import LOGGER

import numpy as np
from api.enrichment.config import PHENOTYPES
from api.dae_query import load_gene_set2
from api.enrichment.results import EnrichmentTestBuilder
from api.precompute import register
from django.conf import settings
from api.enrichment.denovo_counters import DenovoEventsCounter, \
    DenovoGenesEventCounter
from api.enrichment.families import ChildrenStats


class EnrichmentView(APIView):
    def __init__(self):
        self.data = {}

    @staticmethod
    def enrichment_prepare(data):
        if data['denovoStudies']:
            del data['denovoStudies']
        data['denovoStudies'] = 'ALL WHOLE EXOME'

        result = {'denovoStudies': prepare_denovo_studies(data),
                  'geneSet': prepare_string_value(data, 'geneSet'),
                  'geneTerm': prepare_string_value(data, 'geneTerm'),
                  'gene_set_phenotype': prepare_string_value(
                        data,
                        'gene_set_phenotype'),
                  'geneSyms': combine_gene_syms(data)}

        if 'geneSet' not in result or result['geneSet'] is None or \
           'geneTerm' not in result or result['geneTerm'] is None:
            del result['geneSet']
            del result['geneTerm']
            del result['gene_set_phenotype']

        if 'geneSet' in result and result['geneSet'] != 'denovo':
            del result['gene_set_phenotype']

        if not all(result.values()):
            return None

        dsts = result['denovoStudies']
        result['denovoStudies'] = [st for st in dsts
                                   if st.get_attr('study.type') == 'WE']

        return result

    def colormap_value(self, p_val, lessmore):
        scale = 0
        if p_val > 0:
            if p_val > 0.05:
                scale = 0
            else:
                scale = -np.log10(p_val)
                if scale > 5:
                    scale = 5
                elif scale < 0:
                    scale = 0

        intensity = int((5.0 - scale) * 255.0 / 5.0)
        if lessmore == 'more':
            color = "rgba(%d,%d,%d,180)" % (255, intensity, intensity)
        elif lessmore == 'less':
            color = "rgba(%d,%d,%d,180)" % (intensity, intensity, 255)
        else:
            color = "rgb(255,255,255)"
        return color

    def serialize_response_common_data(self):
        res = {}
        res['gs_id'] = self.gene_set

        if self.gene_set is None:
            gene_terms = None
        else:
            gene_terms = load_gene_set2(self.gene_set, self.gene_set_phenotype)

        if self.gene_set and self.gene_term and gene_terms:
            res['gs_desc'] = "%s: %s" % (self.gene_term,
                                         gene_terms.tDesc[self.gene_term])
        else:
            syms = list(self.gene_syms)
            desc = ','.join(sorted(syms))
            res['gs_desc'] = desc
            res['gs_id'] = desc

        res['gene_number'] = len(self.gene_syms)
        res['phenotypes'] = PHENOTYPES
        return res

    def serialize_response_test(self, t):
        tres = {}
        tres['overlap'] = t.total
        tres['count'] = t.count

        tres['label'] = t.name
        if t.type == 'rec':
            tres['syms'] = t.gene_syms.intersection(self.gene_syms)
        tres['filter'] = t.filter

        if t.p_val >= 0.0001:
            tres['p_val'] = round(t.p_val, 4)
        else:
            tres['p_val'] = str('%.1E' % t.p_val)

        tres['expected'] = round(t.expected, 4)

        if t.count > t.expected:
            lessmore = 'more'
        elif t.count > t.expected:
            lessmore = 'less'
        else:
            lessmore = 'equal'

        tres['lessmore'] = lessmore
        tres['bg'] = self.colormap_value(t.p_val, lessmore)
        return tres

    def serialize_response_results(self):
        result = {}
        for phenotype, tests in self.result.items():
            res = []
            for t in tests:
                tres = self.serialize_response_test(t)
                res.append(tres)
            result[phenotype] = res
        return result

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
    def denovo_studies(self):
        return self.data.get('denovoStudies', None)

    @property
    def enrichment_config(self):
        config = settings.ENRICHMENT_CONFIG
        background_name = config['background']
        counter_name = config['denovo_counter']

        if register.has_key(background_name):  # @IgnorePep8
            background = register.get(background_name)
        else:
            background = register.get('synonymous_background')

        if counter_name == 'events_counter':
            counter_cls = DenovoEventsCounter
        elif counter_name == 'genes_counter':
            counter_cls = DenovoGenesEventCounter
        else:
            raise KeyError('wrong denovo counter: {}'.format(counter_name))

        return {'background': background,
                'denovo_counter': counter_cls}

    def get(self, request):
        query_data = prepare_query_dict(request.QUERY_PARAMS)
        LOGGER.info(log_filter(
                request,
                "enrichment query by phenotype: %s" % str(query_data)))

        self.data = self.enrichment_prepare(query_data)

        if self.data is None:
            return Response(None)

        config = self.enrichment_config

        self.enrichment = EnrichmentTestBuilder()
        self.enrichment.build(**config)

        self.result = self.enrichment.calc(self.denovo_studies,
                                           self.gene_syms)

        response = self.serialize()
        response['children_stats'] = ChildrenStats.build(self.denovo_studies)

        return Response(response)
