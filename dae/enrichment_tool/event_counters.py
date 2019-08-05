'''
Created on Nov 7, 2016

@author: lubo
'''
import itertools

from dae.variants.attributes import Sex


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
        syms = set([ge.symbol.upper() for aa in v.alt_alleles
                    for ge in aa.effect.genes])
        not_seen = [gs for gs in syms if (v.family_id + gs) not in seen]
        if not not_seen:
            continue
        for gs in not_seen:
            seen.add(v.family_id + gs)
        res.append(not_seen)

    return res


def get_sym_2_fn(vs):
    gn_sorted = sorted([
        [ge.symbol.upper(), v] for v in vs for aa in v.alt_alleles
        for ge in aa.effect.genes
    ])
    sym_2_vars = {sym: [t[1] for t in tpi]
                  for sym, tpi in itertools.groupby(gn_sorted,
                                                    key=lambda x: x[0])}
    sym_2_fn = {sym: len(set([v.family_id for v in vs]))
                for sym, vs in list(sym_2_vars.items())}
    return sym_2_fn


def filter_denovo_one_gene_per_recurrent_events(vs):
    sym_2_fn = get_sym_2_fn(vs)
    return [[gs] for gs, fn in list(sym_2_fn.items()) if fn > 1]


def filter_denovo_one_gene_per_events(vs):
    sym_2_fn = get_sym_2_fn(vs)
    return [[gs] for gs, _fn in list(sym_2_fn.items())]


class EnrichmentResult(object):
    """
    Represents result of enrichment tool calculations. Supported fields are:

    `name`

    `events` -- list of events found

    `overlapped` -- list of overlapped events

    `expected` -- number of expected events

    `pvalue`
    """

    def __init__(self, name):
        self.name = name
        self.events = None
        self.overlapped = None
        self.expected = None
        self.pvalue = None

    def __repr__(self):
        return "EnrichmentResult({}): events={}; overlapped={}; " \
            "expected={:.2g}; pvalue={:.2g}".format(
                self.name, len(self.events), len(self.overlapped),
                self.expected, self.pvalue)


def filter_overlapping_events(events, gene_syms):
    return [ev for ev in events if any([gs in gene_syms for gs in ev])]


def overlap_enrichment_result_dict(enrichment_results, gene_syms):
    gene_syms = [gs.upper() for gs in gene_syms]

    for enrichment_result in list(enrichment_results.values()):
        enrichment_result.overlapped = filter_overlapping_events(
            enrichment_result.events, gene_syms)

    return enrichment_results


class CounterBase(object):

    @staticmethod
    def counters():
        return {
            'enrichmentEventsCounting': EventsCounter,
            'enrichmentGeneCounting': GeneEventsCounter
        }

    # def get_variants(self, denovo_studies, in_child, effect_types):
    #     variants = []
    #     for st in denovo_studies:
    #         vs = st.get_denovo_variants(
    #             inChild=in_child, effectTypes=effect_types)
    #         variants.append(vs)
    #     return list(itertools.chain(*variants))

    def events(self, variants):
        raise NotImplementedError()

    def _create_event_result(self):
        return {
            'all': EnrichmentResult('all'),
            'rec': EnrichmentResult('rec'),
            'male': EnrichmentResult('male'),
            'female': EnrichmentResult('female'),
            'unspecified': EnrichmentResult('unspecified'),
        }

    def _set_result_events(self, all_events, rec_events,
                           male_events, female_events,
                           unspecified_events):
        result = self._create_event_result()
        result['all'].events = all_events
        result['rec'].events = rec_events
        result['male'].events = male_events
        result['female'].events = female_events
        result['unspecified'].events = unspecified_events
        return result


class EventsCounter(CounterBase):

    def events(self, variants):
        male_variants = [v for v in variants for aa in v.alt_alleles
                         if Sex.male in aa.variant_in_sexes]
        female_variants = [v for v in variants for aa in v.alt_alleles
                           if Sex.female in aa.variant_in_sexes]
        unspecified_variants = [v for v in variants for aa in v.alt_alleles
                                if Sex.unspecified in aa.variant_in_sexes]

        all_events = filter_denovo_one_event_per_family(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_event_per_family(male_variants)
        female_events = filter_denovo_one_event_per_family(female_variants)
        unspecified_events = filter_denovo_one_event_per_family(
            unspecified_variants)

        result = self._set_result_events(
            all_events, rec_events,
            male_events, female_events, unspecified_events)
        return result


class GeneEventsCounter(CounterBase):

    def events(self, variants):
        male_variants = [v for v in variants for aa in v.alt_alleles
                         if Sex.male in aa.variant_in_sexes]
        female_variants = [v for v in variants for aa in v.alt_alleles
                           if Sex.female in aa.variant_in_sexes]
        unspecified_variants = [v for v in variants for aa in v.alt_alleles
                                if Sex.unspecified in aa.variant_in_sexes]

        all_events = filter_denovo_one_gene_per_events(variants)
        rec_events = filter_denovo_one_gene_per_recurrent_events(variants)
        male_events = filter_denovo_one_gene_per_events(male_variants)
        female_events = filter_denovo_one_gene_per_events(female_variants)
        unspecified_events = filter_denovo_one_gene_per_events(
            unspecified_variants)

        result = self._set_result_events(
            all_events, rec_events, male_events, female_events,
            unspecified_events)
        return result
