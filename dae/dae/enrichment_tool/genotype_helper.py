from typing import Optional, cast, Iterable
from dataclasses import dataclass

from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant, FamilyAllele
from dae.studies.study import GenotypeData
from dae.person_sets import PersonSetCollection


@dataclass(frozen=True)
class GeneEffect:
    gene: str
    effect: str


@dataclass(frozen=True)
class AlleleEvent:
    persons: set[tuple[str, str]]
    # person_sets: set[str]
    effect_genes: set[GeneEffect]


@dataclass(frozen=True)
class VariantEvent:
    family_id: str
    fvuid: str
    allele_events: list[AlleleEvent]


class GenotypeHelper:
    """Genotype helper for enrichment tools."""

    def __init__(
            self, genotype_data: GenotypeData,
            person_set_collection: PersonSetCollection,
            effect_types: Optional[list[str]] = None):

        self.genotype_data = genotype_data
        self.person_set_collection = person_set_collection

        denovo_variants = self.genotype_data.query_variants(
            effect_types=effect_types,
            inheritance=str(Inheritance.denovo.name))

        self._denovo_events = self.collect_denovo_events(denovo_variants)

    @staticmethod
    def collect_denovo_events(
        denovo_variants: Iterable[FamilyVariant]
    ) -> list[VariantEvent]:
        """Collect denovo events."""
        result = []
        for fv in denovo_variants:
            allele_events = []
            for aa in fv.alt_alleles:
                fa = cast(FamilyAllele, aa)
                gene_effects = set()
                if fa.effects is None or fa.effects.genes is None:
                    continue
                for ge in fa.effects.genes:
                    if ge.symbol is None or ge.effect is None:
                        continue
                    gene_effects.add(GeneEffect(ge.symbol.upper(), ge.effect))
                persons = set(fa.variant_in_members_fpid)
                allele_events.append(
                    AlleleEvent(
                        persons,
                        gene_effects
                    ))
            result.append(
                VariantEvent(
                    fv.family_id,
                    fv.fvuid,
                    allele_events
                )
            )

        return result

    def get_denovo_events(self) -> list[VariantEvent]:
        return self._denovo_events
