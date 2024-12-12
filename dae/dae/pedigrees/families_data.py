from __future__ import annotations

import copy
import logging
from collections import defaultdict
from collections.abc import (
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    ValuesView,
)
from typing import (
    Any,
)

import pandas as pd

from dae.pedigrees.family import (
    Family,
    Person,
    get_pedigree_column_names,
)
from dae.pedigrees.family_tag_builder import FamilyTagsBuilder
from dae.pedigrees.layout import Layout
from dae.variants.attributes import Role, Sex, Status

logger = logging.getLogger(__name__)


def merge_families(
    l_fam: Family,
    r_fam: Family, *,
    forced: bool = True,
) -> Family:
    """Merge two families into one."""
    assert l_fam.family_id == r_fam.family_id, \
        ("Merging families is only allowed with matching family IDs!"
            f" ({l_fam.family_id} != {r_fam.family_id})")

    if l_fam == r_fam:
        return r_fam

    people_intersection = \
        set(l_fam.persons.keys()) & set(r_fam.persons.keys())

    merged_persons = {}
    merged_persons.update(l_fam.persons)
    merged_persons.update(r_fam.persons)

    for person_id in people_intersection:
        l_person = l_fam.persons[person_id]
        r_person = r_fam.persons[person_id]

        # Use the other person if this one is generated
        if l_person.generated or l_person.missing:
            merged_persons[person_id] = r_person
            continue
        if r_person.generated or r_person.missing:
            merged_persons[person_id] = l_person
            continue

        if l_person.sex == Sex.unspecified:
            merged_persons[person_id] = r_person
        elif r_person.sex == Sex.unspecified:
            merged_persons[person_id] = l_person
        elif l_person.status == Status.unspecified:
            merged_persons[person_id] = r_person
        elif r_person.status == Status.unspecified:
            merged_persons[person_id] = l_person
        elif l_person.role == Role.unknown:
            merged_persons[person_id] = r_person
        elif r_person.role == Role.unknown:
            merged_persons[person_id] = l_person

        match = (l_person.sex == r_person.sex
                 or l_person.sex == Sex.unspecified
                 or r_person.sex == Sex.unspecified) \
            and (l_person.status == r_person.status
                 or l_person.status == Status.unspecified
                 or r_person.status == Status.unspecified) \
            and (l_person.role == r_person.role
                 or l_person.role == Role.unknown
                 or r_person.role == Role.unknown) \
            and (l_person.family_id == r_person.family_id)
        if not match:
            messages = l_person.diff(r_person)
            logger.warning(
                "different definitions for person %s: %s",
                l_person, " ".join(messages))
            if forced:
                logger.warning(
                    "second person %s overwrites the first %s",
                    r_person, l_person)
                merged_persons[person_id] = r_person
            else:
                raise AssertionError(messages)

    # Construct new instances of Person to avoid
    # modifying the original family's Person instances
    # pylint: disable=protected-access
    merged = Family.from_persons([
        Person(**person._attributes)  # noqa: SLF001
        for person in merged_persons.values()
    ])
    layouts = Layout.from_family(merged)
    for layout in layouts:
        layout.apply_to_family(merged)

    tagger = FamilyTagsBuilder()
    tagger.tag_family(merged)

    return merged


class FamiliesData(Mapping[str, Family]):
    """Defines class for handling families in a study."""

    def __init__(self) -> None:
        self._ped_df: pd.DataFrame | None = None
        self._families: dict[str, Family] = {}
        self.persons_by_person_id: dict[str, list[Person]] = defaultdict(list)
        self.persons: dict[tuple[str, str], Person] = {}
        self._broken: dict[str, Family] = {}
        self._real_persons: dict[tuple[str, str], Person] | None = None

    def __deepcopy__(self, memo: dict[int, Any]) -> FamiliesData:
        families_data = FamiliesData()
        families_data._families = copy.deepcopy(  # noqa: SLF001
            self._families, memo)
        families_data._real_persons = copy.deepcopy(  # noqa: SLF001
            self._real_persons, memo)
        families_data.persons = copy.deepcopy(self.persons, memo)
        families_data.persons_by_person_id = copy.deepcopy(
            self.persons_by_person_id, memo)

        return families_data

    def redefine(self) -> None:
        """Rebuild all families."""
        error_msgs = []

        self.persons_by_person_id = defaultdict(list)
        self.persons = {}

        self._ped_df = None
        self._real_persons = None

        all_families = self._families.values()
        self._families = {}
        for family in all_families:
            family.redefine()

            if len(family) == 0:
                self._broken[family.family_id] = family

            self._families[family.family_id] = family

            for person in family.full_members:
                if person.person_id not in self.persons_by_person_id:
                    self.persons_by_person_id[person.person_id].append(person)
                    self.persons[person.fpid] = person
                    continue

                other_persons = self.persons_by_person_id[person.person_id]
                logger.warning(
                    "person %s included in more "
                    "than one family: %s",
                    person, other_persons)
                if person.fpid not in self.persons:
                    self.persons_by_person_id[person.person_id].append(person)
                    self.persons[person.fpid] = person
                    continue

                other_person = self.persons[person.fpid]
                if other_person.missing:
                    self.persons[person.fpid] = person
                    self.persons_by_person_id[person.person_id].append(
                        person)
                    continue
                if person.missing:
                    self.persons_by_person_id[person.person_id].append(
                        person)
                    continue
                diff = person.diff(other_person)
                if diff:
                    error_msgs.append(
                        f"multiple different definitions for person "
                        f"{person.person_id}: "
                        f"{', '.join(diff)}; "
                        f"{other_persons}")
                self.persons_by_person_id[person.person_id].append(
                    person)
        if error_msgs:
            raise AttributeError("; ".join(error_msgs))

    @property
    def broken_families(self) -> dict[str, Family]:
        return self._broken

    @property
    def real_persons(self) -> dict[tuple[str, str], Person]:
        """Return a subset of individuals that are not generated."""
        if self._real_persons is None:
            self._real_persons = {}
            for person in self.persons.values():
                if not person.generated and not person.missing:
                    self._real_persons[person.fpid] = person
        return self._real_persons

    @staticmethod
    def from_family_persons(
            family_persons: dict[str, list[Person]]) -> FamiliesData:
        """Build a families data object from persons grouped by family."""
        families_data = FamiliesData()
        for family_id, persons in family_persons.items():
            assert all(isinstance(p, Person) for p in persons), persons

            family = Family.from_persons(persons)
            # pylint: disable=protected-access
            families_data._families[family_id] = family  # noqa: SLF001
        families_data.redefine()
        return families_data

    @staticmethod
    def from_pedigree_df(ped_df: pd.DataFrame) -> FamiliesData:
        """Build a families data object from a pedigree data frame."""
        persons = defaultdict(list)
        columns = ped_df.columns.tolist()
        for rec in [
            dict(zip(columns, data, strict=True)) for data in ped_df.to_numpy()
        ]:
            person = Person(**rec)
            persons[person.family_id].append(person)

        return FamiliesData.from_family_persons(persons)

    @staticmethod
    def from_families(families: dict[str, Family]) -> FamiliesData:
        """Build families data from dictionary of families."""
        return FamiliesData.from_family_persons(
            {fam.family_id: fam.full_members for fam in families.values()},
        )

    def pedigree_samples(self) -> list[str]:
        return [
            member.sample_id
            for family in self.values()
            for member in family.members_in_order
        ]

    @property
    def ped_df(self) -> pd.DataFrame:
        """Build a pedigree dataframe from a families data."""
        if self._ped_df is None:
            # build ped_df
            column_names: set[str] = set()
            records = []
            for family in self.values():
                for person in family.full_members:
                    # pylint: disable=protected-access
                    rec = copy.deepcopy(person._attributes)  # noqa: SLF001
                    rec["mom_id"] = person.mom_id or "0"
                    rec["dad_id"] = person.dad_id or "0"
                    rec["generated"] = person.generated or False
                    rec["not_sequenced"] = person.not_sequenced or False
                    tags = person.all_tag_labels()
                    rec.update(tags)
                    column_names = column_names.union(set(rec.keys()))
                    records.append(rec)
            columns = get_pedigree_column_names(column_names)
            ped_df = pd.DataFrame.from_records(records, columns=columns)
            self._ped_df = ped_df
        return self._ped_df

    def copy(self) -> FamiliesData:
        """Build a copy of a families data object."""
        return copy.deepcopy(self)

    def __getitem__(self, family_id: str) -> Family:
        return self._families[family_id]

    def __len__(self) -> int:
        return len(self._families)

    def __iter__(self) -> Iterator[str]:
        return iter(self._families)

    def __contains__(self, family_id: Any) -> bool:
        return family_id in self._families

    def __delitem__(self, family_id: str) -> None:
        del self._families[family_id]

    def keys(self) -> KeysView[str]:
        return self._families.keys()

    def values(self) -> ValuesView[Family]:
        return self._families.values()

    def items(self) -> ItemsView[str, Family]:
        return self._families.items()

    def get(  # type: ignore
        self, key: str,
        default: Family | None = None,
    ) -> Family | None:
        return self._families.get(key, default)

    def persons_without_parents(self) -> list[Person]:
        """Return list of persons without parents."""
        return [
            person
            for fam in self._families.values()
            for person in fam.members_in_order
            if fam.member_is_parent(person.person_id)
        ]

    def persons_with_parents(self) -> list[Person]:
        """Return list of persons with both parents."""
        return [
            person
            for fam in self._families.values()
            for person in fam.members_in_order
            if fam.member_has_both_parents(person.person_id)
        ]

    def persons_with_roles(
        self,
        roles: list[Role] | None = None,
        family_ids: Iterable[str] | None = None,
    ) -> list[Person]:
        """Return list of persons matching the specified roles."""
        if family_ids is None:
            persons = self.real_persons.values()
        else:
            persons = filter(
                lambda p: p.family_id in set(family_ids),  # type: ignore
                self.real_persons.values())

        if roles is None:
            return list(persons)

        if not isinstance(roles[0], Role):
            roles_q = {Role.from_name(role) for role in roles}
        else:
            roles_q = set(roles)

        return list(
            filter(lambda m: m.role in roles_q, persons))

    def families_of_persons(self, person_ids: set[str]) -> set[str]:
        family_ids: set[str] = set()
        for person_id in person_ids:
            family_ids = family_ids.union(
                {p.family_id for p in self.persons_by_person_id[person_id]})
        return family_ids

    @staticmethod
    def combine(
            first: FamiliesData, second: FamiliesData, *,
            forced: bool = True) -> FamiliesData:
        """Combine families from two families data objects."""
        all_families = set(first.keys()) | set(second.keys())
        combined_dict: dict[str, Family] = {}
        mismatched_families = []
        for fid in all_families:
            if fid in first and fid in second:
                try:
                    combined_dict[fid] = merge_families(
                        first[fid], second[fid], forced=forced)
                except AssertionError:
                    logger.exception(
                        "mismatched families: %s, %s",
                        first[fid], second[fid])
                    mismatched_families.append(fid)
            elif fid in first:
                combined_dict[fid] = first[fid]
            elif fid in second:
                combined_dict[fid] = second[fid]

        if len(mismatched_families) > 0:
            logger.warning("mismatched families: %s", mismatched_families)
            if not forced:
                assert len(mismatched_families) == 0, mismatched_families
            else:
                logger.warning("second family overwrites family definition")

        return FamiliesData.from_families(combined_dict)


def tag_families_data(families: FamiliesData) -> None:
    builder = FamilyTagsBuilder()
    for family in families.values():
        builder.clear_tags(family)
        builder.tag_family(family)
        builder.tag_family_type(family)
