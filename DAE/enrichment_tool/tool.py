'''
Created on Nov 8, 2016

@author: lubo
'''


class EnrichmentTool(object):

    def __init__(self, denovo_studies, children_stats,
                 background, event_counter):
        self.denovo_studies = denovo_studies
        self.background = background
        self.event_counter = event_counter
        self.children_stats = children_stats

    def calc(self, phenotype, effect_types, gene_syms):
        counter = self.event_counter(phenotype, effect_types)
        events = counter.events(self.denovo_studies)
        overlapped_events, stats = self.background.calc_stats(
            events, gene_syms, self.children_stats[phenotype])
        return events, overlapped_events, stats
