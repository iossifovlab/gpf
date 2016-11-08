'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.config import ChildrenStats


class EnrichmentTool(object):

    def __init__(self, denovo_studies, background, event_counter):
        self.denovo_studies = denovo_studies
        self.background = background
        self.event_counter = event_counter
        self.children_stats = ChildrenStats.build(denovo_studies)

    def calc(self, phenotype, effect_types, gene_syms):
        counter = self.event_counter(phenotype, effect_types)
        events = counter.events(self.denovo_studies)
        stats = self.background.calc_stats(
            events, gene_syms, self.children_stats[phenotype])
        return events, stats
