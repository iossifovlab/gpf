from __future__ import annotations

import itertools

from typing import Type, Iterable
from dataclasses import dataclass

from dae.variants.attributes import Sex
from dae.enrichment_tool.genotype_helper import VariantEvent


def filter_denovo_one_event_per_family(
    variant_events: list[VariantEvent],
    requested_effect_types: Iterable[str]
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
    for ve in variant_events:
        syms = set(
            ge.gene
            for ae in ve.allele_events
            for ge in ae.effect_genes
            if ge.effect in requested_effect_types
        )
        not_seen_genes = [gs for gs in syms if (ve.family_id + gs) not in seen]
        if not not_seen_genes:
            continue
        for gene_sym in not_seen_genes:
            seen.add(ve.family_id + gene_sym)
        res.append(not_seen_genes)
    return res


def get_sym_2_fn(
    variant_events: list[VariantEvent],
    requested_effect_types: Iterable[str]
) -> dict[str, int]:
    """Count the number of requested effect types events in genes."""
    gn_sorted = sorted(
        [
            [ge.gene, ve]
            for ve in variant_events
            for ae in ve.allele_events
            for ge in ae.effect_genes
            if ge.effect in requested_effect_types
        ],
        key=lambda x: (x[0], x[1].fvuid),  # type: ignore
    )
    sym_2_vars: dict[str, list[VariantEvent]] = {
        sym: [t[1] for t in tpi]  # type: ignore
        for sym, tpi in itertools.groupby(gn_sorted, key=lambda x: x[0])
    }
    sym_2_fn = {
        sym: len(set(ve.family_id for ve in variant_events))
        for sym, variant_events in list(sym_2_vars.items())
    }
    return sym_2_fn


def filter_denovo_one_gene_per_recurrent_events(
    variant_events: list[VariantEvent],
    requsted_effect_types: Iterable[str]
) -> list[list[str]]:
    """Collect only events that occur in more than one family."""
    sym_2_fn = get_sym_2_fn(variant_events, requsted_effect_types)
    res = [[gs] for gs, fn in list(sym_2_fn.items()) if fn > 1]
    return res


def filter_denovo_one_gene_per_events(
    variant_events: list[VariantEvent], requested_effect_types: Iterable[str]
) -> list[list[str]]:
    sym_2_fn = get_sym_2_fn(variant_events, requested_effect_types)
    res = [[gs] for gs, _fn in list(sym_2_fn.items())]
    return res


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
        self, variant_events: list[VariantEvent],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        raise NotImplementedError()


class EventsCounter(CounterBase):
    """Events counter class."""

    def events(
        self, variant_events: list[VariantEvent],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if all_children & ae.persons
        ]
        male_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if male_children & ae.persons
        ]
        female_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if female_children & ae.persons
        ]
        unspecified_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if unspecified_children & ae.persons
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
        self, variant_events: list[VariantEvent],
        children_by_sex: dict[str, set[tuple[str, str]]],
        effect_types: Iterable[str]
    ) -> EventsCounterResult:
        """Count the events by sex and effect type."""
        male_children = children_by_sex[Sex.male.name]
        female_children = children_by_sex[Sex.female.name]
        unspecified_children = children_by_sex[Sex.unspecified.name]
        all_children = male_children | female_children | unspecified_children

        all_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if all_children & ae.persons
        ]
        male_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if male_children & ae.persons
        ]
        female_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if female_children & ae.persons
        ]
        unspecified_variants = [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if unspecified_children & ae.persons
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
