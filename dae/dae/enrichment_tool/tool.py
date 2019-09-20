class EnrichmentTool(object):

    def __init__(self, config, background, event_counter):
        self.config = config

        self.background = background
        self.event_counter = event_counter

    def calc(self, effect_types, gene_syms, variants, children_stats):
        enrichment_events = self.event_counter.events(variants)
        self.background.calc_stats(
            effect_types, enrichment_events, gene_syms, children_stats)
        return enrichment_events
