class EnrichmentTool(object):
    def __init__(self, config, background, event_counter):
        self.config = config

        self.background = background
        self.event_counter = event_counter

    def calc(self, effect_types, gene_syms, variants, children_by_sex):
        from dae.utils.effect_utils import expand_effect_types

        requested_effect_types = expand_effect_types(effect_types)
        enrichment_events = self.event_counter.events(
            variants, children_by_sex, requested_effect_types
        )
        self.background.calc_stats(
            effect_types, enrichment_events, gene_syms, children_by_sex
        )
        return enrichment_events
