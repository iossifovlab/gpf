from collections import defaultdict
from typing import Any, Optional, cast

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family
from dae.person_sets import PersonSetCollection


def get_family_pedigree(
    family: Family,
    person_set_collection: PersonSetCollection,
) -> list:
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


def get_family_type(
    family: Family, person_to_set: dict,
) -> tuple:
    """Transform a family into a tuple of strings describing members."""
    family_type = []
    # get family size
    family_type.append(str(len(family.members_in_order)))
    members_by_role = sorted(
        family.members_in_order, key=lambda p: str(p.role),
    )
    members_by_role_and_sex = sorted(members_by_role, key=lambda p: str(p.sex))
    for person in members_by_role_and_sex:
        # get person set collection value
        if person.fpid not in person_to_set:
            raise ValueError(f"person {person.fpid} in found in person sets")

        set_value = person_to_set[person.fpid]
        family_type.append(
            f"{set_value}.{person.role}.{person.sex}.{person.status}",
        )
    return tuple(family_type)


class FamilyCounter:
    """Class representing a family counter JSON."""

    def __init__(self, json: dict[str, Any]) -> None:
        self.families = json["families"]
        self.pedigree = json["pedigree"]
        self.pedigrees_count = json["pedigrees_count"]
        self.tags: Optional[list] = None

        tags = json.get("tags")
        if tags is not None:
            self.tags = list(tags)
        self.counter_id = int(json["counter_id"])

    @property
    def family(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.families[0])

    @staticmethod
    def from_family(
        family: Family,
        pedigree: list, label: Optional[int] = None,
    ) -> "FamilyCounter":
        return FamilyCounter({
            "families": [family.family_id],
            "pedigree": pedigree,
            "pedigrees_count": (
                label if label is not None else family.family_id
            ),
            "tags": family.tag_labels,
            "counter_id": 0,
        })

    def to_dict(self, full: bool = False) -> dict[str, Any]:
        """Transform counter to dict."""
        output = {
            "pedigree": self.pedigree,
            "pedigrees_count": self.pedigrees_count,
            "tags": self.tags,
            "counter_id": self.counter_id,
        }

        if full:
            output["families"] = self.families

        return output


class FamiliesGroupCounters:
    """Class representing families group counters JSON."""

    def __init__(self, json: dict[str, Any]) -> None:
        self.group_name = json["group_name"]
        self.phenotypes = json["phenotypes"]
        self.legend = json["legend"]
        counters = [FamilyCounter(d) for d in json["counters"]]
        self.counters = {c.counter_id: c for c in counters}

    # FIXME: Too many locals
    @staticmethod
    def from_families(  # pylint: disable=too-many-locals
        families: FamiliesData,
        person_set_collection: PersonSetCollection,
        draw_all_families: bool,
    ) -> "FamiliesGroupCounters":
        """Create families group counters from a dict of families."""
        counters: dict[tuple, FamilyCounter] = {}

        if draw_all_families:
            for idx, family in enumerate(families.values()):
                family_counter = FamilyCounter({
                    "families": [family.family_id],
                    "pedigree": get_family_pedigree(
                        family, person_set_collection,
                    ),
                    "pedigrees_count": family.family_id,
                    "tags": family.tag_labels,
                    "counter_id": idx,
                })
                counters[(family.family_id,)] = family_counter
        else:
            families_to_types: dict[tuple, list[Family]] = defaultdict(list)

            person_to_set = {}
            for person_set in person_set_collection.person_sets.values():
                for person_id in person_set.persons:
                    person_to_set[person_id] = person_set.id

            for family in families.values():
                families_to_types[
                    get_family_type(family, person_to_set)
                ].append(family)

            families_to_types = dict(
                sorted(
                    families_to_types.items(),
                    key=lambda item: len(item[1]), reverse=True,
                ),
            )

            for idx, items in enumerate(families_to_types.items()):
                family_type, families_of_type = items
                pedigree_label = str(len(families_of_type))

                family = families_of_type[0]
                counter = FamilyCounter({
                    "families": [f.family_id for f in families_of_type],
                    "pedigree": get_family_pedigree(
                        family, person_set_collection,
                    ),
                    "tags": family.tag_labels,
                    "pedigrees_count": pedigree_label,
                    "counter_id": idx,
                })
                counters[family_type] = counter

        json = {
            "group_name": person_set_collection.name,
            "phenotypes": list(person_set_collection.person_sets.keys()),
            "counters": [
                counter.to_dict(full=True) for counter in counters.values()
            ],
            "legend": [
                {"id": domain.id, "name": domain.name, "color": domain.color}
                for domain in person_set_collection.person_sets.values()
            ],
        }

        return FamiliesGroupCounters(json)

    def to_dict(self, full: bool = False) -> dict[str, Any]:
        return {
            "group_name": self.group_name,
            "phenotypes": self.phenotypes,
            "counters": [
                counter.to_dict(full=full)
                for counter in self.counters.values()
            ],
            "legend": self.legend,
        }
