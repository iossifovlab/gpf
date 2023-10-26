from typing import Iterable, Any

from dae.utils.effect_utils import expand_effect_types
from dae.variants.family_variant import FamilyVariant

from dae.enrichment_tool.genotype_helper import children_stats
from dae.enrichment_tool.base_enrichment_background import \
    BaseEnrichmentBackground
from dae.enrichment_tool.event_counters import CounterBase, \
    EnrichmentResult


class EnrichmentTool:
    """Construct and run enrichment tool test."""

    def __init__(
        self, config: dict[str, Any],
        background: BaseEnrichmentBackground,
        event_counter: CounterBase
    ):
        self.config = config

        self.background = background
        self.event_counter = event_counter

    def calc(
        self,
        gene_syms: Iterable[str],
        variants: list[FamilyVariant],
        effect_types: Iterable[str],
        children_by_sex: dict[str, set[tuple[str, str]]]
    ) -> dict[str, EnrichmentResult]:
        """Perform the enrichment tool test."""
        requested_effect_types = expand_effect_types(effect_types)
        enrichment_events = self.event_counter.events(
            variants, children_by_sex, requested_effect_types
        )
        return self.background.calc_enrichment_test(
            enrichment_events, gene_syms,
            effect_types=effect_types,
            children_stats=children_stats(children_by_sex)
        )
