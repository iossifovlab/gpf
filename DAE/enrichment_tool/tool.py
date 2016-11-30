'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.config import children_stats_counter


class EnrichmentTool(object):

    def __init__(self, background, event_counter):
        self.background = background
        self.event_counter = event_counter

    def calc(self, denovo_studies, in_child, effect_types, gene_syms,
             children_stats=None):
        if children_stats is None:
            children_stats = children_stats_counter(denovo_studies, in_child)

        enrichment_results = self.event_counter.events(
            denovo_studies, in_child, effect_types)
        self.background.calc_stats(
            effect_types, enrichment_results, gene_syms, children_stats)
        return enrichment_results
