from typing import Iterable

from box import Box

from dae.utils.effect_utils import expand_effect_types
from dae.variants.family_variant import FamilyVariant

from dae.enrichment_tool.background import BackgroundBase
from dae.enrichment_tool.event_counters import CounterBase, EnrichmentResult


class EnrichmentTool:
    """Construct and run enrichment tool test."""

    def __init__(
        self, config: Box,
        background: BackgroundBase,
        event_counter: CounterBase
    ):
        self.config = config

        self.background = background
        self.event_counter = event_counter

    def calc(
        self, effect_types: Iterable[str],
        gene_syms: Iterable[str],
        variants: list[FamilyVariant],
        children_by_sex: dict[str, set[str]]
    ) -> dict[str, EnrichmentResult]:
        """Perform the enrichment tool test."""
        requested_effect_types = expand_effect_types(effect_types)
        enrichment_events = self.event_counter.events(
            variants, children_by_sex, requested_effect_types
        )
        self.background.calc_stats(
            effect_types, enrichment_events, gene_syms, children_by_sex
        )
        return enrichment_events
