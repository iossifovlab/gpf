from typing import Optional, cast, Iterable
from collections import Counter, defaultdict
from dataclasses import dataclass

from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant, FamilyAllele
from dae.studies.study import GenotypeData
from dae.person_sets import PersonSetCollection


@dataclass
class ChildrenStats:
    male: int
    female: int
    unspecified: int


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
        # self.person_set = person_set_collection.person_sets[person_set_id]
        self._children_stats: dict[str, ChildrenStats] = {}
        self._children_by_sex: dict[str, dict[str, set[tuple[str, str]]]] = {}

        denovo_variants = self.genotype_data.query_variants(
            effect_types=effect_types,
            inheritance=str(Inheritance.denovo.name))

        self._denovo_events = self.collect_denovo_events(denovo_variants)
        self._build_children_stats()

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
                # person_sets = set()
                # for fpid in persons:
                #     person_set = \
                #         person_set_collection.get_person_set_of_person(fpid)
                #     person_sets.add(person_set.id)
                allele_events.append(
                    AlleleEvent(
                        persons,
                        # person_sets,
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

    def _build_children_stats(self) -> None:
        families = self.genotype_data.families
        children = families.persons_with_parents()
        for person_set_id, person_set in \
                self.person_set_collection.person_sets.items():
            children_by_sex: dict[str, set[tuple[str, str]]] = defaultdict(set)
            seen = set()
            for person in children:
                if person.fpid in seen:
                    continue

                if person.fpid not in person_set.persons:
                    continue

                children_by_sex[person.sex.name].add(person.fpid)
                seen.add(person.fpid)
            self._children_by_sex[person_set_id] = children_by_sex
            self._children_stats[person_set_id] = children_stats(
                children_by_sex)

    def get_denovo_events(self) -> list[VariantEvent]:
        return self._denovo_events

    def children_by_sex(
        self, person_set_id: str
    ) -> dict[str, set[tuple[str, str]]]:
        return self._children_by_sex[person_set_id]

    def get_children_stats(self, person_set_id: str) -> ChildrenStats:
        return self._children_stats[person_set_id]


def children_stats(
    children_by_sex: dict[str, set[tuple[str, str]]]
) -> ChildrenStats:
    counter: dict[str, int] = Counter()
    for sex, persons in children_by_sex.items():
        counter[sex] = len(persons)
    return ChildrenStats(
        counter["M"],
        counter["F"],
        counter["U"]
    )
