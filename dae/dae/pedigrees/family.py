"""Defines classes representing individuals and families."""

from __future__ import annotations

import copy
import logging

from typing import Iterator, KeysView, ValuesView, ItemsView, \
    Optional, Any, Iterable
from enum import Enum, auto
from collections import defaultdict
from collections.abc import Mapping

import pandas as pd

from dae.utils.helpers import isnan
from dae.variants.attributes import Role, Sex, Status


logger = logging.getLogger(__name__)


PEDIGREE_COLUMN_NAMES = {
    "family": "family_id",
    "person": "person_id",
    "mother": "mom_id",
    "father": "dad_id",
    "sex": "sex",
    "status": "status",
    "role": "role",
    "sample id": "sample_id",
    "layout": "layout",
    "generated": "generated",
    "proband": "proband",
    "not_sequenced": "not_sequenced",
    "missing": "missing"
}


class FamilyType(Enum):
    """Family types used in family structure filters."""

    TRIO = auto()
    QUAD = auto()
    MULTIGENERATIONAL = auto()
    SIMPLEX = auto()
    MULTIPLEX = auto()
    OTHER = auto()

    @staticmethod
    def from_name(name: str) -> FamilyType:
        """Construct family type from string."""
        assert isinstance(name, str)
        name = name.lower()
        if name == "trio":
            return FamilyType.TRIO
        if name == "quad":
            return FamilyType.QUAD
        if name == "multigenerational":
            return FamilyType.MULTIGENERATIONAL
        if name == "simplex":
            return FamilyType.SIMPLEX
        if name == "multiplex":
            return FamilyType.MULTIPLEX
        if name == "other":
            return FamilyType.OTHER
        raise ValueError(f"unexpected family type name: {name}")


ALL_FAMILY_TYPES = set([
    FamilyType.TRIO,
    FamilyType.QUAD,
    FamilyType.MULTIGENERATIONAL,
    FamilyType.SIMPLEX,
    FamilyType.MULTIPLEX,
    FamilyType.OTHER,
])


class Person:
    """Class to represent an individual."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, **attributes: Any):
        self._attributes = attributes
        self.redefine()

    def redefine(self) -> None:
        # pylint: disable=too-many-branches
        """Extract attributes and turns them into properties."""
        assert "person_id" in self._attributes
        self.family_id = self._attributes["family_id"]
        self.family: Optional[Family] = None
        self.person_id = self._attributes["person_id"]
        self.sample_id = self._attributes.get("sample_id", None)
        index = self._attributes.get("index", None)
        if index is not None:
            self.set_attr("member_index", index)
            del self._attributes["index"]
        self.member_index = self._attributes.get("member_index", None)

        self._sex = Sex.from_name(self._attributes["sex"])
        if "role" not in self._attributes:
            self._role = None
        else:
            self._role = Role.from_name(self._attributes.get("role"))

        self._status = Status.from_name(self._attributes["status"])

        self._attributes["sex"] = self._sex
        self._attributes["role"] = self._role
        self._attributes["status"] = self._status

        self.mom_id = self.get_attr("mom_id")
        if self.mom_id == "0":
            self.mom_id = None
            self._attributes["mom_id"] = None
        self.dad_id = self.get_attr("dad_id")
        if self.dad_id == "0":
            self.dad_id = None
            self._attributes["dad_id"] = None
        self.mom: Optional[Person] = None
        self.dad: Optional[Person] = None
        assert self.mom_id is None or isinstance(self.mom_id, str), \
            (self, self._attributes)
        assert self.dad_id is None or isinstance(self.dad_id, str), \
            (self, self._attributes)
        if self._attributes.get("not_sequenced"):
            value = self._attributes.get("not_sequenced")
            if value in {"None", "0", "False"}:
                self._attributes["not_sequenced"] = None
        if self._attributes.get("generated"):
            value = self._attributes.get("generated")
            if value in {True, "True", "1", "yes"}:
                self._attributes["generated"] = True
            else:
                self._attributes["generated"] = False

        if self._attributes.get("missing"):
            value = self._attributes.get("missing")
            if value in {True, "True", "1", "yes"}:
                self._attributes["missing"] = True
            else:
                self._attributes["missing"] = None

    def __repr__(self) -> str:
        decorator = ""
        if self.generated:
            decorator = "[G] "
        elif self.not_sequenced:
            decorator = "[N] "
        return f"Person({decorator}{self.person_id} ({self.family_id}); " \
            f"{self.role}; {self.sex}, {self.status})"

    def to_json(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "person_id": self.person_id,
            "dad_id": self.dad_id,
            "mom_id": self.mom_id,
            "sample_id": self.sample_id,
            "member_index": self.member_index,
            "sex": str(self.sex),
            "role": str(self.role),
            "status": str(self.status),
            "layout": self.layout,
            "generated": self.generated,
            "family_bin": self.family_bin,
            "not_sequenced": self.not_sequenced,
            "missing": self.missing,
        }

    @property
    def role(self) -> Optional[Role]:
        return self._role

    @property
    def sex(self) -> Sex:
        return self._sex

    @property
    def status(self) -> Status:
        return self._status

    @property
    def layout(self) -> Optional[str]:
        return self._attributes.get("layout", None)

    @property
    def generated(self) -> bool:
        return self._attributes.get("generated", False)

    @property
    def not_sequenced(self) -> bool:
        return self.generated or \
            self._attributes.get("not_sequenced", False)

    @property
    def missing(self) -> bool:
        return bool(
            self.generated or self.not_sequenced
            or self._attributes.get("missing", False))

    @property
    def family_bin(self) -> Optional[str]:
        return self._attributes.get("family_bin", None)

    @property
    def sample_index(self) -> Optional[int]:
        return self._attributes.get("sample_index", None)

    def has_mom(self) -> bool:
        return self.mom is not None

    def has_dad(self) -> bool:
        return self.dad is not None

    def has_parent(self) -> bool:
        return self.has_dad() or self.has_mom()

    def has_both_parents(self) -> bool:
        return self.has_dad() and self.has_mom()

    def has_missing_parent(self) -> bool:
        if self.dad is None or self.mom is None:
            return True
        assert self.dad is not None
        assert self.mom is not None
        return self.dad.missing or self.mom.missing

    def has_no_parent(self) -> bool:
        if self.dad is None or self.mom is None:
            return True
        assert self.dad is not None
        assert self.mom is not None
        return self.dad.missing and self.mom.missing

    def has_attr(self, key: str) -> bool:
        return key in self._attributes

    def get_attr(self, key: str, default: Any = None) -> Any:
        res = self._attributes.get(key, default)
        if isinstance(res, float) and isnan(res):
            return None
        return res

    def set_attr(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Person):
            return False
        return self.person_id == other.person_id and \
            self.family_id == other.family_id and \
            self.sex == other.sex and \
            self.role == other.role and \
            self.status == other.status and \
            self.mom_id == other.mom_id and \
            self.dad_id == other.dad_id and \
            self.generated == other.generated and \
            self.not_sequenced == other.not_sequenced

    def diff(self, other: Any) -> None:
        """Print difference between two individuals."""
        if self.person_id != other.person_id:
            print(f"{self}  person_id:", self.person_id, other.person_id)
        if self.family_id != other.family_id:
            print(f"{self}  family_id:", self.family_id, other.family_id)
        if self.sex != other.sex:
            print(f"{self}        sex:", self.sex, other.sex)
        if self.role != other.role:
            print(f"{self}       role:", self.role, other.role)
        if self.status != other.status:
            print(f"{self}      status:", self.status, other.status)
        if self.mom_id != other.mom_id:
            print(f"{self}      mom_id:", self.mom_id, other.mom_id)
        if self.dad_id != other.dad_id:
            print(f"{self}      dad_id:", self.dad_id, other.dad_id)
        if self.generated != other.generated:
            print(f"{self}   generated:", self.generated, other.generated)
        if self.not_sequenced != other.not_sequenced:
            print(
                f"{self} not_sequenced:",
                self.not_sequenced, other.not_sequenced)


class Family:
    """Defines class to represent a family."""

    def __init__(self, family_id: str):
        self.family_id = family_id
        self.persons: dict[str, Person] = {}
        self._samples_index: Optional[tuple[Optional[int], ...]] = None
        self._members_in_order: Optional[list[Person]] = None
        self._trios: Optional[dict[str, tuple[str, str, str]]] = None
        self._tags: set[str] = set()

    def add_tag(self, tag: str) -> None:
        self._tags.add(tag)

    @property
    def tags(self) -> set[str]:
        return self._tags

    def _connect_family(self) -> None:
        index = 0
        for member in self.persons.values():
            member.family = self
            member.mom = self.get_member(member.mom_id)
            member.dad = self.get_member(member.dad_id)
            if member.missing:
                member.member_index = -1
            else:
                member.member_index = index
                index += 1

    @staticmethod
    def from_persons(persons: list[Person]) -> Family:
        """Create a family from list of persons."""
        assert len(persons) > 0
        assert all(persons[0].family_id == p.family_id for p in persons)
        family_id = persons[0].family_id

        family = Family(family_id)
        for index, person in enumerate(persons):
            person.set_attr("member_index", index)
            family.persons[person.person_id] = person
        family._connect_family()  # pylint: disable=protected-access
        assert all(p.family is not None for p in family.persons.values())

        return family

    @staticmethod
    def from_records(records: dict) -> Family:
        persons = []
        for rec in records:
            person = Person(**rec)
            persons.append(person)
        return Family.from_persons(persons)

    def __len__(self) -> int:
        return len(self.members_in_order)

    def __repr__(self) -> str:
        return f"Family({self.family_id}, {list(self.persons.values())})"

    def to_json(self) -> dict:
        return {
            "family_id": self.family_id,
            "person_ids": self.members_ids,
            "samples_index": self._samples_index,
            "family_type": self.family_type.name,
            "tags": self.tags
        }

    def get_columns(self) -> list[str]:
        """Collect list of columns for representing a family as data frame."""
        column_names = set(
            self.members_in_order[0]  # pylint: disable=protected-access
                ._attributes.keys())
        columns = [
            col
            for col in PEDIGREE_COLUMN_NAMES.values()
            if col in column_names
            or col in ["generated", "not_sequenced"]
        ]
        extension_columns = column_names.difference(set(columns))
        extension_columns = extension_columns.difference(
            set(["sample_index"])
        )
        columns.extend(sorted(extension_columns))
        return columns

    def add_members(self, persons: list[Person]) -> None:
        assert all(isinstance(p, Person) for p in persons)
        assert all(p.family_id == self.family_id for p in persons)

        for person in persons:
            self.persons[person.person_id] = person
        self.redefine()

    def redefine(self) -> None:
        self._members_in_order = None
        self._trios = None
        self._samples_index = None
        self._connect_family()

    @property
    def full_members(self) -> list[Person]:
        return list(self.persons.values())

    @property
    def members_in_order(self) -> list[Person]:
        """Return list of family members in the order of definition."""
        if self._members_in_order is None:
            self._members_in_order = list(
                filter(
                    lambda m: not m.missing and not m.generated,
                    self.persons.values())
            )
        return self._members_in_order

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Family):
            return False
        if len(self.full_members) != len(other.full_members):
            return False
        for member1, member2 in zip(self.full_members, other.full_members):
            if member1 != member2:
                return False
        return True

    def has_members(self) -> bool:
        return len(self.members_in_order) > 0

    @property
    def members_ids(self) -> list[str]:
        return [m.person_id for m in self.members_in_order]

    @property
    def trios(self) -> dict[str, tuple[str, str, str]]:
        """Split family into list of trios - child, mom and dad."""
        if self._trios is None:
            self._trios = {}
            members = {m.person_id: m for m in self.members_in_order}
            for pid, person in list(members.items()):
                if person.mom_id in members and person.dad_id in members:
                    self._trios[pid] = (pid, person.mom_id, person.dad_id)
        return self._trios

    @property
    def samples_index(self) -> tuple[Optional[int], ...]:
        if self._samples_index is None:
            self._samples_index = tuple(
                m.sample_index for m in self.members_in_order)
        return self._samples_index

    @property
    def family_type(self) -> FamilyType:
        """Calculate the type of the family."""
        # pylint: disable=too-many-return-statements
        has_grandparent = any(
            person.role in (
                Role.maternal_grandfather,
                Role.maternal_grandmother,
                Role.paternal_grandfather,
                Role.paternal_grandmother
            ) for person in self.persons.values())

        unaffected_parents = all(
            person.status is Status.unaffected
            for person in self.get_members_with_roles([Role.mom, Role.dad]))

        affected_siblings = any(
            person.status is Status.affected
            for person in self.get_members_with_roles([Role.sib]))

        if has_grandparent:
            return FamilyType.MULTIGENERATIONAL
        if unaffected_parents:
            if len(self.persons) == 3:
                return FamilyType.TRIO
            if len(self.persons) == 4 and not affected_siblings:
                return FamilyType.QUAD
            if affected_siblings:
                return FamilyType.MULTIPLEX
        else:
            if affected_siblings:
                return FamilyType.MULTIPLEX
            return FamilyType.SIMPLEX
        return FamilyType.OTHER

    @staticmethod
    def merge(l_fam: Family, r_fam: Family, forced: bool = True) -> Family:
        """Merge two families into one."""
        assert l_fam.family_id == r_fam.family_id, \
            ("Merging families is only allowed with matching family IDs!"
             f" ({l_fam.family_id} != {r_fam.family_id})")

        people_intersection = \
            set(l_fam.persons.keys()) & set(r_fam.persons.keys())

        merged_persons = {}
        merged_persons.update(l_fam.persons)
        merged_persons.update(r_fam.persons)

        for person_id in people_intersection:
            l_person = l_fam.persons[person_id]
            r_person = r_fam.persons[person_id]

            # Use the other person if this one is generated
            if l_person.generated:
                merged_persons[person_id] = r_person
            elif r_person.generated:
                merged_persons[person_id] = l_person
            elif l_person.sex == Sex.unspecified:
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
                message = f"mismatched attributes for person {person_id}; " \
                    f"sex[{l_person.sex} == {r_person.sex}], " \
                    f"status[{l_person.status} == {r_person.status}], " \
                    f"role[{l_person.role} == {r_person.role}], " \
                    f"family[{l_person.family_id} == {r_person.family_id}]"

                logger.warning(message)
                if forced:
                    logger.warning("second person overwrites: %s", r_person)
                    merged_persons[person_id] = r_person
                else:
                    raise AssertionError(message)

        # Construct new instances of Person to avoid
        # modifying the original family's Person instances
        return Family.from_persons([
            Person(**person._attributes)  # pylint: disable=protected-access
            for person in merged_persons.values()
        ])

    def members_index(
        self, person_ids: list[str]
    ) -> list[Optional[int]]:
        index = []
        for pid in person_ids:
            index.append(self.persons[pid].member_index)
        return index

    def get_member(
        self, person_id: str
    ) -> Optional[Person]:
        return self.persons.get(person_id, None)

    def get_members_with_roles(
        self, roles: list[Role]
    ) -> list[Person]:
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        return list(filter(lambda m: m.role in roles, self.members_in_order))

    def get_members_with_statuses(
        self, statuses: list[Status]
    ) -> list[Person]:
        if not isinstance(statuses[0], Status):
            statuses = [Status.from_name(status) for status in statuses]
        return list(
            filter(lambda m: m.status in statuses, self.members_in_order)
        )


class FamiliesData(Mapping[str, Family]):
    """Defines class for handling families in a study."""

    def __init__(self) -> None:
        self._ped_df: Optional[pd.DataFrame] = None
        self._families: dict[str, Family] = {}
        self.persons: dict[str, Person] = {}
        self._broken: dict[str, Family] = {}
        self._person_ids_with_parents = None
        self._real_persons: Optional[dict[str, Person]] = None
        self._families_by_type: dict[FamilyType, set[str]] = {}

    def redefine(self) -> None:
        """Rebuild all families."""
        error_msgs = []

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
                if person.person_id in self.persons:
                    logger.error(
                        "person %s included in more "
                        "than one family: %s, %s",
                        person.person_id, family.family_id,
                        self.persons[person.person_id].family_id)
                    error_msgs.append(
                        f"person {person.person_id} "
                        f"in multiple families")
                self.persons[person.person_id] = person
        if error_msgs:
            raise AttributeError("; ".join(error_msgs))

    @property
    def broken_families(self) -> dict[str, Family]:
        return self._broken

    @property
    def real_persons(self) -> dict[str, Person]:
        """Return a subset of individuals that are not generated."""
        if self._real_persons is None:
            self._real_persons = {}
            for person in self.persons.values():
                if not person.generated and not person.missing:
                    self._real_persons[person.person_id] = person
        return self._real_persons

    @property
    def families_by_type(self) -> dict[FamilyType, set[str]]:
        """Build a dictionary of families by type."""
        if not self._families_by_type:
            for family_id, family in self._families.items():
                self._families_by_type.setdefault(
                    family.family_type, set()
                ).add(family_id)
        return self._families_by_type

    @staticmethod
    def from_family_persons(
            family_persons: dict[str, list[Person]]) -> FamiliesData:
        """Build a families data object from persons grouped by family."""
        families_data = FamiliesData()
        for family_id, persons in family_persons.items():
            assert all(isinstance(p, Person) for p in persons), persons

            family = Family.from_persons(persons)
            # pylint: disable=protected-access
            families_data._families[family_id] = family
            for person_id, person in family.persons.items():
                families_data.persons[person_id] = person
        return families_data

    @staticmethod
    def from_pedigree_df(ped_df: pd.DataFrame) -> FamiliesData:
        """Build a families data object from a pedigree data frame."""
        persons = defaultdict(list)
        for rec in ped_df.to_dict(orient="records"):
            person = Person(**rec)  # type: ignore
            persons[person.family_id].append(person)

        fams = FamiliesData.from_family_persons(persons)
        return fams

    @staticmethod
    def from_families(families: dict[str, Family]) -> FamiliesData:
        """Build families data from dictionary of families."""
        families_data = FamiliesData.from_family_persons(
            {fam.family_id: fam.full_members for fam in families.values()}
        )

        return families_data

    def pedigree_samples(self) -> list[str]:
        result = []
        for family in self.values():
            for member in family.members_in_order:
                result.append(member.sample_id)
        return result

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
                    rec = copy.deepcopy(person._attributes)
                    rec["mom_id"] = person.mom_id if person.mom_id else "0"
                    rec["dad_id"] = person.dad_id if person.dad_id else "0"
                    rec["generated"] = person.generated \
                        if person.generated else False
                    rec["not_sequenced"] = person.not_sequenced \
                        if person.not_sequenced else False
                    column_names = column_names.union(set(rec.keys()))
                    records.append(rec)
            columns = [
                col
                for col in PEDIGREE_COLUMN_NAMES.values()
                if col in column_names
            ]
            extention_columns = column_names.difference(set(columns))
            extention_columns = extention_columns.difference(
                set(["sample_index"])
            )
            columns.extend(sorted(extention_columns))
            ped_df = pd.DataFrame.from_records(records, columns=columns)
            self._ped_df = ped_df
        return self._ped_df

    def copy(self) -> FamiliesData:
        """Build a copy of a families data object."""
        return FamiliesData.from_pedigree_df(self.ped_df)

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
        default: Optional[Family] = None
    ) -> Optional[Family]:
        return self._families.get(key, default)

    # def families_query_by_person_ids(self, person_ids):
    #     res = {}
    #     for person_id in person_ids:
    #         person = self.persons.get(person_id)
    #         if person is None:
    #             continue
    #         if person.family_id in res:
    #             continue
    #         family = self._families[person.family_id]
    #         res[family.family_id] = family
    #     return res

    def persons_without_parents(self) -> list[Person]:
        """Return list of persons without parents."""
        result: list[Person] = []
        for fam in list(self._families.values()):
            for person in fam.members_in_order:
                if person.has_no_parent():
                    result.append(person)
        return result

    def persons_with_parents(self) -> list[Person]:
        """Return list of persons with both parents."""
        result: list[Person] = []
        for fam in list(self._families.values()):
            for person in fam.members_in_order:
                if person.has_both_parents() and \
                        not person.has_missing_parent():
                    result.append(person)
        return result

    def persons_with_roles(
        self,
        roles: Optional[list[Role]] = None,
        family_ids: Optional[Iterable[str]] = None
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
            roles_q = set(Role.from_name(role) for role in roles)
        else:
            roles_q = set(roles)

        return list(
            filter(lambda m: m.role in roles_q, persons))

    def families_of_persons(self, person_ids: set[str]) -> set[str]:
        family_ids: set[str] = set()
        for person_id in person_ids:
            family_ids.add(self.persons[person_id].family_id)
        return family_ids

    @staticmethod
    def combine(
            first: FamiliesData, second: FamiliesData,
            forced: bool = True) -> FamiliesData:
        """Combine families from two families data objects."""
        same_families = set(first.keys()) & \
            set(second.keys())
        combined_dict: dict[str, Family] = {}
        combined_dict.update(first)
        combined_dict.update(second)
        mismatched_families = []
        for fid in same_families:
            try:
                combined_dict[fid] = Family.merge(
                    first[fid], second[fid], forced=forced)
            except AssertionError:
                logger.error(
                    "mismatched families: %s, %s",
                    first[fid], second[fid], exc_info=True)

                mismatched_families.append(fid)

        if len(mismatched_families) > 0:
            logger.warning("mismatched families: %s", mismatched_families)
            if not forced:
                assert len(mismatched_families) == 0, mismatched_families
            else:
                logger.warning("second family overwrites family definition")

        return FamiliesData.from_families(combined_dict)
