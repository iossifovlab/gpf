"""
Created on Nov 7, 2016

@author: lubo
"""
import itertools

from dae.variants.attributes import Sex


def filter_denovo_one_event_per_family(vs, requested_effect_types):
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
        syms = set(
            [
                ge.symbol.upper()
                for aa in v.alt_alleles
                for ge in aa.effects.genes
                if ge.effect in requested_effect_types
            ]
        )
        not_seen_genes = [gs for gs in syms if (v.family_id + gs) not in seen]
        if not not_seen_genes:
            continue
        for gs in not_seen_genes:
            seen.add(v.family_id + gs)
        res.append(not_seen_genes)

    return res


def get_sym_2_fn(vs, requested_effect_types):
    gn_sorted = sorted(
        [
            [ge.symbol.upper(), v]
            for v in vs
            for aa in v.alt_alleles
            for ge in aa.effects.genes
            if ge.effect in requested_effect_types
        ]
    )
    sym_2_vars = {
        sym: [t[1] for t in tpi]
        for sym, tpi in itertools.groupby(gn_sorted, key=lambda x: x[0])
    }
    sym_2_fn = {
        sym: len(set([v.family_id for v in vs]))
        for sym, vs in list(sym_2_vars.items())
    }
    return sym_2_fn


def filter_denovo_one_gene_per_recurrent_events(vs, requsted_effect_types):
    sym_2_fn = get_sym_2_fn(vs, requsted_effect_types)
    return [[gs] for gs, fn in list(sym_2_fn.items()) if fn > 1]


def filter_denovo_one_gene_per_events(vs, requested_effect_types):
    sym_2_fn = get_sym_2_fn(vs, requested_effect_types)
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
        return (
            "EnrichmentResult({}): events={}; overlapped={}; "
            "expected={}; pvalue={}".format(
                self.name,
                len(self.events) if self.events else None,
                len(self.overlapped) if self.overlapped else None,
                self.expected,
                self.pvalue,
            )
        )


def filter_overlapping_events(events, gene_syms):
    return [ev for ev in events if any([gs in gene_syms for gs in ev])]


def overlap_enrichment_result_dict(enrichment_results, gene_syms):
    gene_syms = [gs.upper() for gs in gene_syms]

    for enrichment_result in list(enrichment_results.values()):
        enrichment_result.overlapped = filter_overlapping_events(
            enrichment_result.events, gene_syms
        )

    return enrichment_results


class CounterBase(object):
    @staticmethod
    def counters():
        return {
            "enrichment_events_counting": EventsCounter,
            "enrichment_gene_counting": GeneEventsCounter,
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
            "all": EnrichmentResult("all"),
            "rec": EnrichmentResult("rec"),
            "male": EnrichmentResult("male"),
            "female": EnrichmentResult("female"),
            "unspecified": EnrichmentResult("unspecified"),
        }

    def _set_result_events(
        self,
        all_events,
        rec_events,
        male_events,
        female_events,
        unspecified_events,
    ):
        result = self._create_event_result()
        result["all"].events = all_events
        result["rec"].events = rec_events
        result["male"].events = male_events
        result["female"].events = female_events
        result["unspecified"].events = unspecified_events
        return result


class EventsCounter(CounterBase):
    def events(self, variants, children_by_sex, effect_types):
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if all_children & set(aa.variant_in_members)
        ]
        male_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if male_children & set(aa.variant_in_members)
        ]
        female_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if female_children & set(aa.variant_in_members)
        ]
        unspecified_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if unspecified_children in set(aa.variant_in_members)
        ]

        all_events = filter_denovo_one_event_per_family(
            all_variants, effect_types
        )
        rec_events = filter_denovo_one_gene_per_recurrent_events(
            all_variants, effect_types
        )
        male_events = filter_denovo_one_event_per_family(
            male_variants, effect_types
        )
        female_events = filter_denovo_one_event_per_family(
            female_variants, effect_types
        )
        unspecified_events = filter_denovo_one_event_per_family(
            unspecified_variants, effect_types
        )

        result = self._set_result_events(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )
        return result


class GeneEventsCounter(CounterBase):
    def events(self, variants, children_by_sex, effect_types):
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if all_children & set(aa.variant_in_members)
        ]
        male_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if male_children & set(aa.variant_in_members)
        ]
        female_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if female_children & set(aa.variant_in_members)
        ]
        unspecified_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if unspecified_children in set(aa.variant_in_members)
        ]

        all_events = filter_denovo_one_gene_per_events(
            all_variants, effect_types
        )
        rec_events = filter_denovo_one_gene_per_recurrent_events(
            all_variants, effect_types
        )
        male_events = filter_denovo_one_gene_per_events(
            male_variants, effect_types
        )
        female_events = filter_denovo_one_gene_per_events(
            female_variants, effect_types
        )
        unspecified_events = filter_denovo_one_gene_per_events(
            unspecified_variants, effect_types
        )

        result = self._set_result_events(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )
        return result
