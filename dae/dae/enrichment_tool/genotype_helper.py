from collections import Counter, defaultdict

from dae.variants.attributes import Inheritance


class GenotypeHelper(object):
    def __init__(
        self, genotype_data_group, person_set_collection, person_set_id
    ):
        self.genotype_data_group = genotype_data_group
        self.person_set_collection = person_set_collection
        self.person_set = person_set_collection.person_sets[person_set_id]
        self._children_stats = None
        self._children_by_sex = None

    def get_variants(self, effect_types):
        families_group = self.genotype_data_group.get_families_group(
            self.person_set_collection.id
        )
        assert families_group is not None
        people_with_people_group = set(self.person_set.persons.keys())

        # TODO: Remove this when genotype_data_study.query_variants can
        # support non expand_effect_types as LGDs
        from dae.utils.effect_utils import expand_effect_types

        effect_types = expand_effect_types(effect_types)

        variants = self.genotype_data_group.query_variants(
            inheritance=str(Inheritance.denovo.name),
            person_ids=people_with_people_group,
            effect_types=set(effect_types),
        )

        return list(variants)

    def children_by_sex(self):
        if self._children_by_sex is None:
            self._children_by_sex = defaultdict(set)
            seen = set()

            for p in self.genotype_data_group.families.persons_with_parents():
                iid = "{}:{}".format(p.family_id, p.person_id)
                if iid in seen:
                    continue

                if p.person_id not in self.person_set.persons:
                    continue

                self._children_by_sex[p.sex.name].add(p.person_id)
                seen.add(iid)
        return self._children_by_sex

    def get_children_stats(self):
        if self._children_stats is not None:
            return self._children_stats
        counter = Counter()
        persons_by_sex = self.children_by_sex()
        for sex, persons in persons_by_sex.items():
            counter[sex] = len(persons)
        self._children_stats = counter

        return self._children_stats
