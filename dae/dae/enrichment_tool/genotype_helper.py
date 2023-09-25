from typing import Optional
from collections import Counter, defaultdict

from dae.variants.attributes import Inheritance, Role
from dae.variants.family_variant import FamilyVariant
from dae.studies.study import GenotypeData
from dae.person_sets import PersonSetCollection


class GenotypeHelper:
    """Genotype helper for enrichment tools."""

    def __init__(
            self, genotype_data: GenotypeData,
            person_set_collection: PersonSetCollection,
            effect_types: Optional[set[str]] = None):

        self.genotype_data = genotype_data
        self.person_set_collection = person_set_collection
        # self.person_set = person_set_collection.person_sets[person_set_id]
        self._children_stats: dict[str, dict[str, int]] = {}
        self._children_by_sex: dict[str, dict[str, set[str]]] = {}

        self._denovo_variants = list(
            self.genotype_data.query_variants(
                effect_types=effect_types,
                inheritance=str(Inheritance.denovo.name)))

        self._build_children_stats()

    def _build_children_stats(self) -> None:
        families = self.genotype_data.families
        children = list(
            families.persons_with_roles(
                roles=[Role.prb, Role.sib, Role.child]))
        for person_set_id, person_set in \
                self.person_set_collection.person_sets.items():
            children_by_sex: dict[str, set[str]] = defaultdict(set)
            seen = set()
            for person in children:
                if person.fpid in seen:
                    continue

                if person.fpid not in person_set.persons:
                    continue

                children_by_sex[person.sex.name].add(person.fpid)
                seen.add(person.fpid)
            self._children_by_sex[person_set_id] = children_by_sex
            counter: dict[str, int] = Counter()
            for sex, persons in children_by_sex.items():
                counter[sex] = len(persons)
            self._children_stats[person_set_id] = counter

    def get_denovo_variants(self) -> list[FamilyVariant]:
        return self._denovo_variants

    def children_by_sex(self, person_set_id: str) -> dict[str, set[str]]:
        return self._children_by_sex[person_set_id]

    def get_children_stats(self, person_set_id: str) -> dict[str, int]:
        return self._children_stats[person_set_id]
