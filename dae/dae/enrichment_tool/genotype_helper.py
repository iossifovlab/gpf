from collections import Counter, defaultdict

from dae.variants.attributes import Inheritance, Role


class GenotypeHelper(object):
    def __init__(
            self, genotype_data, person_set_collection, effect_types=None):

        self.genotype_data = genotype_data
        self.person_set_collection = person_set_collection
        # self.person_set = person_set_collection.person_sets[person_set_id]
        self._children_stats = {}
        self._children_by_sex = {}

        self._denovo_variants = self.genotype_data.query_variants(
            effect_types=effect_types,
            inheritance=str(Inheritance.denovo.name))
        self._denovo_variants = list(self._denovo_variants)

        self._build_children_stats()

    def _build_children_stats(self):
        families = self.genotype_data.families
        children = list(
            families.persons_with_roles(
                    roles=[Role.prb, Role.sib, Role.child]))

        for person_set_id, person_set in \
                self.person_set_collection.person_sets.items():
            children_by_sex = defaultdict(set)
            seen = set()
            for p in children:
                iid = "{}:{}".format(p.family_id, p.person_id)
                if iid in seen:
                    continue

                if p.person_id not in person_set.persons:
                    continue

                children_by_sex[p.sex.name].add(p.person_id)
                seen.add(iid)
            self._children_by_sex[person_set_id] = children_by_sex
            counter = Counter()
            for sex, persons in children_by_sex.items():
                counter[sex] = len(persons)
            self._children_stats[person_set_id] = counter

    def get_denovo_variants(self):
        return self._denovo_variants

    def children_by_sex(self, person_set_id):
        return self._children_by_sex[person_set_id]

    def get_children_stats(self, person_set_id):
        return self._children_stats[person_set_id]
