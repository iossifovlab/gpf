from __future__ import annotations

import itertools

from typing import Type, cast, Iterable
from dataclasses import dataclass

from dae.variants.attributes import Sex
from dae.effect_annotation.effect import AlleleEffects
from dae.variants.family_variant import FamilyVariant, FamilyAllele


def filter_denovo_one_event_per_family(
    vs: list[FamilyVariant], requested_effect_types: Iterable[str]
) -> list[list[str]]:
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
            ge.symbol.upper()
            for aa in v.alt_alleles
            for ge in cast(AlleleEffects, aa.effects).genes
            if ge.effect in requested_effect_types
        )
        not_seen_genes = [gs for gs in syms if (v.family_id + gs) not in seen]
        if not not_seen_genes:
            continue
        for gene_sym in not_seen_genes:
            seen.add(v.family_id + gene_sym)
        res.append(not_seen_genes)

    return res


def get_sym_2_fn(
    vs: list[FamilyVariant], requested_effect_types: Iterable[str]
) -> dict[str, int]:
    """Count the number of requested effected events in genes."""
    gn_sorted = sorted(
        [
            [ge.symbol.upper(), v]
            for v in vs
            for aa in v.alt_alleles
            for ge in cast(AlleleEffects, aa.effects).genes
            if ge.effect in requested_effect_types
        ]
    )
    sym_2_vars = {
        sym: [t[1] for t in tpi]
        for sym, tpi in itertools.groupby(gn_sorted, key=lambda x: x[0])
    }
    sym_2_fn = {
        sym: len(set(v.family_id for v in vs))
        for sym, vs in list(sym_2_vars.items())
    }
    return sym_2_fn


def filter_denovo_one_gene_per_recurrent_events(
    vs: list[FamilyVariant], requsted_effect_types: Iterable[str]
) -> list[list[str]]:
    sym_2_fn = get_sym_2_fn(vs, requsted_effect_types)
    return [[gs] for gs, fn in list(sym_2_fn.items()) if fn > 1]


def filter_denovo_one_gene_per_events(
    vs: list[FamilyVariant], requested_effect_types: Iterable[str]
) -> list[list[str]]:
    sym_2_fn = get_sym_2_fn(vs, requested_effect_types)
    return [[gs] for gs, _fn in list(sym_2_fn.items())]


@dataclass
class EventsCounterResult:
    all: list[list[str]]
    rec: list[list[str]]
    male: list[list[str]]
    female: list[list[str]]
    unspecified: list[list[str]]


class EnrichmentResult:
    """Represents result of enrichment tool calculations.

    Supported fields are:

    `name`

    `events` -- list of events found

    `overlapped` -- list of overlapped events

    `expected` -- number of expected events

    `pvalue`
    """

    def __init__(
        self, name: str,
        events: list[list[str]],
        overlapped: list[list[str]],
        expected: float,
        pvalue: float
    ):
        self.name: str = name
        self.events = events
        self.overlapped = overlapped
        self.expected = expected
        self.pvalue = pvalue

    def __repr__(self) -> str:
        return f"EnrichmentResult({self.name}): " \
            f"events={len(self.events) if self.events else None}; " \
            f"overlapped=" \
            f"{len(self.overlapped) if self.overlapped else None}; " \
            f"expected={self.expected}; pvalue={self.pvalue}"


def filter_overlapping_events(
        events: list[list[str]], gene_syms: list[str]) -> list[list[str]]:
    return [ev for ev in events if any(gs in gene_syms for gs in ev)]


def overlap_enrichment_result_dict(
    events_counts: EventsCounterResult, gene_syms: Iterable[str]
) -> EventsCounterResult:
    """Calculate the overlap between all events and requested gene syms."""
    gene_syms_upper = [gs.upper() for gs in gene_syms]
    result = EventsCounterResult(
        filter_overlapping_events(events_counts.all, gene_syms_upper),
        filter_overlapping_events(events_counts.rec, gene_syms_upper),
        filter_overlapping_events(events_counts.male, gene_syms_upper),
        filter_overlapping_events(events_counts.female, gene_syms_upper),
        filter_overlapping_events(events_counts.unspecified, gene_syms_upper),
    )
    return result


class CounterBase:
    """Class to represent enrichement events counter object."""

    @staticmethod
    def counters() -> dict[str, Type[CounterBase]]:
        return {
            "enrichment_events_counting": EventsCounter,
            "enrichment_gene_counting": GeneEventsCounter,
        }

    def events(
        self, variants: list[FamilyVariant],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        raise NotImplementedError()


class EventsCounter(CounterBase):
    """Events counter class."""

    def events(
        self, variants: list[FamilyVariant],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if all_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        male_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if male_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        female_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if female_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        unspecified_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if unspecified_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
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

        result = EventsCounterResult(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )
        return result


class GeneEventsCounter(CounterBase):
    """Counts events in genes."""

    def events(
        self, variants: list[FamilyVariant],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        """Count the events by sex and effect type."""
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if all_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        male_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if male_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        female_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if female_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
        ]
        unspecified_variants = [
            v
            for v in variants
            for aa in v.alt_alleles
            if unspecified_children
            & set(cast(FamilyAllele, aa).variant_in_members_fpid)
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

        result = EventsCounterResult(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )
        return result
