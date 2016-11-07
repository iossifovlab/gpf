'''
Created on Nov 7, 2016

@author: lubo
'''
import itertools
from enrichment_tool.config import EnrichmentConfig


def filter_denovo_one_event_per_family(vs):
    """
    For each variant returns list of affected gene syms.

    vs - generator for variants.

    This functions receives a generator for variants and transforms each
    variant into list of gene symbols, that are affected by the variant.

    The result is represented as list of lists.
    """
    seen = set()
    res = []
    for v in vs:
        syms = set([ge['sym'].upper() for ge in v.requestedGeneEffects])
        not_seen = [gs for gs in syms if (v.familyId + gs) not in seen]
        if not not_seen:
            continue
        for gs in not_seen:
            seen.add(v.familyId + gs)
        res.append(not_seen)

    return res


def filter_denovo_one_gene_per_recurrent_events(vs):
    gn_sorted = sorted([[ge['sym'].upper(), v] for v in vs
                        for ge in v.requestedGeneEffects])
    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.familyId for v in vs]))
                for sym, vs in sym_2_vars.items()}
    return [[gs] for gs, fn in sym_2_fn.items() if fn > 1]


def filter_denovo_one_gene_per_events(vs):
    gn_sorted = sorted([[ge['sym'].upper(), v] for v in vs
                        for ge in v.requestedGeneEffects])
    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.familyId for v in vs]))
                for sym, vs in sym_2_vars.items()}
    return [[gs] for gs, _fn in sym_2_fn.items()]


class CounterBase(EnrichmentConfig):

    def __init__(self, phenotype, effect_type):
        super(CounterBase, self).__init__(phenotype, effect_type)

    def get_variants(self, denovo_studies):
        studies = denovo_studies.get_studies(self.phenotype)
        variants = []
        for st in studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child, effectTypes=self.effect_type)
            variants.append(vs)
        return list(itertools.chain(*variants))

    def events(self, denovo_studies):
        raise NotImplementedError()


class EventsResult(EnrichmentConfig):

    def __init__(self, config):
        super(EventsResult, self).__init__(
            config.phenotype, config.effect_type)

    def __call__(self, events, rec_events, boys_events, girls_events):
        self.all_events = events
        self.rec_events = rec_events
        self.male_events = boys_events
        self.female_events = girls_events

        self.all_count = len(self.all_events)
        self.rec_count = len(self.rec_events)
        self.male_count = len(self.male_events)
        self.female_count = len(self.female_events)

        return self

    @staticmethod
    def filter_overlapping_events(events, gene_set):
        return [ev for ev in events if any([gs in gene_set for gs in ev])]

    def overlap(self, gene_set):
        gene_syms = [gs.upper() for gs in gene_set]

        all_events = self.filter_overlapping_events(
            self.all_events, gene_syms)
        rec_events = self.filter_overlapping_events(
            self.rec_events, gene_syms)
        male_events = self.filter_overlapping_events(
            self.male_events, gene_syms)
        female_events = self.filter_overlapping_events(
            self.female_events, gene_syms)
        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)


class EventsCounter(CounterBase):

    def __init__(self, phenotype, effect_type):
        super(EventsCounter, self).__init__(phenotype, effect_type)

    def events(self, denovo_studies):
        variants = self.get_variants(denovo_studies)
        male_variants = [v for v in variants if v.inChS[3] == 'M']
        female_variants = [v for v in variants if v.inChS[3] == 'F']

        all_events = filter_denovo_one_event_per_family(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_event_per_family(male_variants)
        female_events = filter_denovo_one_event_per_family(female_variants)

        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)


class GeneEventsCounter(CounterBase):

    def __init__(self, phenotype, effect_type):
        super(GeneEventsCounter, self).__init__(phenotype, effect_type)

    def events(self, denovo_studies):
        variants = self.get_variants(denovo_studies)
        male_variants = [v for v in variants if v.inChS[3] == 'M']
        female_variants = [v for v in variants if v.inChS[3] == 'F']

        all_events = filter_denovo_one_gene_per_events(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_gene_per_events(male_variants)
        female_events = filter_denovo_one_gene_per_events(female_variants)

        return EventsResult(self)(
            all_events, rec_events, male_events, female_events)
