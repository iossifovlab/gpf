from collections import defaultdict

from dae.person_sets import PersonSetCollection


def get_family_pedigree(family, person_set_collection):
    return [
        (
            p.family_id,
            p.person_id,
            p.mom_id if p.mom_id else "0",
            p.dad_id if p.dad_id else "0",
            p.sex.short(),
            str(p.role),
            PersonSetCollection.get_person_color(p, person_set_collection),
            p.layout,
            p.generated,
            "",
            "",
        )
        for p in family.persons.values()
    ]


def get_family_type(family, person_to_set):
    family_type = list()
    # get family size
    family_type.append(str(len(family.members_in_order)))
    members_by_role = sorted(
        family.members_in_order, key=lambda p: str(p.role)
    )
    members_by_role_and_sex = sorted(members_by_role, key=lambda p: str(p.sex))
    for person in members_by_role_and_sex:
        # get person set collection value
        set_value = person_to_set[person.person_id]
        family_type.append(
            f"{set_value}.{person.role}.{person.sex}.{person.status}"
        )
    return tuple(family_type)


class FamilyCounter(object):
    def __init__(self, families, pedigree, family_label):
        self.families = families
        self.pedigree = pedigree
        self.pedigrees_label = family_label

    @property
    def family(self):
        return self.families[0]

    def to_dict(self):
        return {
            "pedigree": self.pedigree,
            "pedigrees_count": self.pedigrees_label,
        }


class FamiliesGroupCounters(object):
    def __init__(
        self,
        families,
        person_set_collection,
        draw_all_families,
        families_count_show_id,
    ):
        self.families = families
        self.person_set_collection = person_set_collection
        self.draw_all_families = draw_all_families
        self.families_count_show_id = families_count_show_id

        self.counters = self._build_counters()

    def _build_counters(self):
        result = dict()

        if self.draw_all_families:
            for family in self.families.values():
                fc = FamilyCounter(
                    [family],
                    get_family_pedigree(family, self.person_set_collection),
                    family.family_id,
                )
                result[family.family_id] = fc
        else:
            families_to_types = defaultdict(list)

            person_to_set = dict()
            for person_set in self.person_set_collection.person_sets.values():
                for person_id in person_set.persons:
                    person_to_set[person_id] = person_set.id

            for family in self.families.values():
                families_to_types[
                    get_family_type(family, person_to_set)
                ].append(family)

            families_to_types = {
                    k: v for k, v in sorted(
                        families_to_types.items(),
                        key=lambda item: len(item[1]), reverse=True)
            }

            for family_type, families in families_to_types.items():
                if (
                    self.families_count_show_id
                    and len(families) <= self.families_count_show_id
                ):
                    pedigree_label = ", ".join(
                        [fam.family_id for fam in families]
                    )
                else:
                    pedigree_label = str(len(families))

                family = families[0]
                fc = FamilyCounter(
                    families,
                    get_family_pedigree(family, self.person_set_collection),
                    pedigree_label,
                )
                result[family_type] = fc

        return result

    def to_dict(self):
        return {
            "group_name": self.person_set_collection.name,
            "phenotypes": list(self.person_set_collection.person_sets.keys()),
            "counters": [
                {
                    "counters": [
                        counter.to_dict() for counter in self.counters.values()
                    ],
                }
            ],
            "legend": [
                {"id": domain.id, "name": domain.name, "color": domain.color}
                for domain in self.person_set_collection.person_sets.values()
            ],
        }
