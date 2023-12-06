from __future__ import annotations
import abc
import itertools

from typing import Type, Iterable
from dataclasses import dataclass

from dae.person_sets import ChildrenBySex
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
class VariantEventsResult:
    all: list[VariantEvent]
    rec: list[VariantEvent]
    male: list[VariantEvent]
    female: list[VariantEvent]
    unspecified: list[VariantEvent]


@dataclass
class EventsResult:
    all: list[list[str]]
    rec: list[list[str]]
    male: list[list[str]]
    female: list[list[str]]
    unspecified: list[list[str]]


@dataclass
class EventCountersResult:
    """Represents result of event counting."""

    all: int
    rec: int
    male: int
    female: int
    unspecified: int

    @staticmethod
    def from_events_result(events: EventsResult) -> EventCountersResult:
        return EventCountersResult(
            len(events.all),
            len(events.rec),
            len(events.male),
            len(events.female),
            len(events.unspecified)
        )


class EnrichmentSingleResult:
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
        events: int,
        overlapped: int,
        expected: float,
        pvalue: float
    ):
        self.name: str = name
        self.events = events
        self.overlapped = overlapped
        self.expected = expected
        self.pvalue = pvalue

    def __repr__(self) -> str:
        return f"EnrichmentSingleResult({self.name}): " \
            f"events={self.events}; " \
            f"overlapped=" \
            f"{self.overlapped}; " \
            f"expected={self.expected}; pvalue={self.pvalue}"


@dataclass
class EnrichmentResult:
    """Represents result of calculating enrichment test."""

    all: EnrichmentSingleResult
    rec: EnrichmentSingleResult
    male: EnrichmentSingleResult
    female: EnrichmentSingleResult
    unspecified: EnrichmentSingleResult


def filter_overlapping_events(
        events: list[list[str]], gene_syms: list[str]) -> list[list[str]]:
    return [ev for ev in events if any(gs in gene_syms for gs in ev)]


def overlap_enrichment_result_dict(
    events_counts: EventsResult, gene_syms: Iterable[str]
) -> EventsResult:
    """Calculate the overlap between all events and requested gene syms."""
    gene_syms_upper = [gs.upper() for gs in gene_syms]
    result = EventsResult(
        filter_overlapping_events(events_counts.all, gene_syms_upper),
        filter_overlapping_events(events_counts.rec, gene_syms_upper),
        filter_overlapping_events(events_counts.male, gene_syms_upper),
        filter_overlapping_events(events_counts.female, gene_syms_upper),
        filter_overlapping_events(events_counts.unspecified, gene_syms_upper),
    )
    return result


def overlap_event_counts(
    events_counts: EventsResult,
    gene_syms: Iterable[str]
) -> EventCountersResult:
    overlapped_events = overlap_enrichment_result_dict(
        events_counts, gene_syms)
    return EventCountersResult(
        len(overlapped_events.all),
        len(overlapped_events.rec),
        len(overlapped_events.male),
        len(overlapped_events.female),
        len(overlapped_events.unspecified)
    )


class CounterBase(abc.ABC):
    """Class to represent enrichement events counter object."""

    @abc.abstractmethod
    def events(
        self, variant_events: list[VariantEvent],
        children_by_sex: ChildrenBySex,
        effect_types: Iterable[str]
    ) -> EventsResult:
        raise NotImplementedError()

    def event_counts(
        self, variant_events: list[VariantEvent],
        children_by_sex: ChildrenBySex,
        effect_types: Iterable[str]
    ) -> EventCountersResult:
        """Calculate the event counts from the given variant events.

        Args:
            variant_events (list[VariantEvent]):
                A list of variant events.
            children_by_sex (dict[str, set[tuple[str, str]]]):
                A dictionary mapping sex to a set of child IDs.
            effect_types (Iterable[str]):
                An iterable of effect types.

        Returns:
            EventCountersResult: An object containing the event counters.

        """
        events_result = self.events(
            variant_events, children_by_sex, effect_types)
        return EventCountersResult(
            len(events_result.all),
            len(events_result.rec),
            len(events_result.male),
            len(events_result.female),
            len(events_result.unspecified)
        )

    def select_events_in_person_set(
        self, variant_events: list[VariantEvent],
        persons: set[tuple[str, str]]
    ) -> list[VariantEvent]:
        """Select variant events that occur in the passed persons."""
        return [
            ve
            for ve in variant_events
            for ae in ve.allele_events
            if persons & ae.persons
        ]

    def split_events(
        self, variant_events: list[VariantEvent],
        children_by_sex: ChildrenBySex,
    ) -> VariantEventsResult:
        """Split the passed variant events based on the children's sex.

        Args:
            variant_events (list[VariantEvent]): The list of variant events
                to be split.
            children_by_sex (dict[str, set[tuple[str, str]]]): A dictionary
                containing children grouped by sex.

        Returns:
            VariantEventsResult: An object containing the split variant events.

        """
        male = children_by_sex.male
        female = children_by_sex.female
        unspecified = children_by_sex.unspecified
        all_children = male | female | unspecified

        return VariantEventsResult(
            self.select_events_in_person_set(variant_events, all_children),
            [],
            self.select_events_in_person_set(variant_events, male),
            self.select_events_in_person_set(variant_events, female),
            self.select_events_in_person_set(variant_events, unspecified)
        )


class EventsCounter(CounterBase):
    """Events counter class."""

    def events(
        self, variant_events: list[VariantEvent],
        children_by_sex: ChildrenBySex,
        effect_types: Iterable[str]
    ) -> EventsResult:
        events_result = self.split_events(variant_events, children_by_sex)
        all_events = filter_denovo_one_event_per_family(
            events_result.all, effect_types
        )
        rec_events = filter_denovo_one_gene_per_recurrent_events(
            events_result.all, effect_types
        )
        male_events = filter_denovo_one_event_per_family(
            events_result.male, effect_types
        )
        female_events = filter_denovo_one_event_per_family(
            events_result.female, effect_types
        )
        unspecified_events = filter_denovo_one_event_per_family(
            events_result.unspecified, effect_types
        )

        return EventsResult(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )


class GeneEventsCounter(CounterBase):
    """Counts events in genes."""

    def events(
        self, variant_events: list[VariantEvent],
        children_by_sex: ChildrenBySex,
        effect_types: Iterable[str]
    ) -> EventsResult:
        """Count the events by sex and effect type."""
        events_result = self.split_events(variant_events, children_by_sex)

        all_events = filter_denovo_one_gene_per_events(
            events_result.all, effect_types
        )
        rec_events = filter_denovo_one_gene_per_recurrent_events(
            events_result.all, effect_types
        )
        male_events = filter_denovo_one_gene_per_events(
            events_result.male, effect_types
        )
        female_events = filter_denovo_one_gene_per_events(
            events_result.female, effect_types
        )
        unspecified_events = filter_denovo_one_gene_per_events(
            events_result.unspecified, effect_types
        )

        result = EventsResult(
            all_events,
            rec_events,
            male_events,
            female_events,
            unspecified_events,
        )
        return result


EVENT_COUNTERS: dict[str, Type[CounterBase]] = {
    "enrichment_events_counting": EventsCounter,
    "enrichment_gene_counting": GeneEventsCounter,
}
