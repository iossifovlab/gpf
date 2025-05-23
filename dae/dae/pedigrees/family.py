"""Defines classes representing individuals and families."""

from __future__ import annotations

import enum
import logging
from collections.abc import Iterable
from typing import Any, cast

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
    "missing": "missing",
}


class FamilyTag(enum.IntEnum):
    """Enumeration of all available family tags."""

    NUCLEAR = enum.auto()
    QUAD = enum.auto()
    TRIO = enum.auto()

    SIMPLEX = enum.auto()
    MULTIPLEX = enum.auto()
    CONTROL = enum.auto()

    AFFECTED_DAD = enum.auto()
    AFFECTED_MOM = enum.auto()
    AFFECTED_PRB = enum.auto()
    AFFECTED_SIB = enum.auto()

    UNAFFECTED_DAD = enum.auto()
    UNAFFECTED_MOM = enum.auto()
    UNAFFECTED_PRB = enum.auto()
    UNAFFECTED_SIB = enum.auto()

    MALE_PRB = enum.auto()
    FEMALE_PRB = enum.auto()

    MISSING_MOM = enum.auto()
    MISSING_DAD = enum.auto()

    @property
    def label(self) -> str:
        return _TAG2LABEL[self]

    @staticmethod
    def from_label(label: str) -> FamilyTag:
        return _LABEL2TAG[label]

    @staticmethod
    def all_labels() -> Iterable[str]:
        return _LABEL2TAG.keys()

    @staticmethod
    def all_tags() -> Iterable[FamilyTag]:
        return _TAG2LABEL.keys()


_LABEL2TAG = {
    "tag_nuclear_family": FamilyTag.NUCLEAR,
    "tag_quad_family": FamilyTag.QUAD,
    "tag_trio_family": FamilyTag.TRIO,
    "tag_simplex_family": FamilyTag.SIMPLEX,
    "tag_multiplex_family": FamilyTag.MULTIPLEX,
    "tag_control_family": FamilyTag.CONTROL,
    "tag_affected_dad_family": FamilyTag.AFFECTED_DAD,
    "tag_affected_mom_family": FamilyTag.AFFECTED_MOM,
    "tag_affected_prb_family": FamilyTag.AFFECTED_PRB,
    "tag_affected_sib_family": FamilyTag.AFFECTED_SIB,
    "tag_unaffected_dad_family": FamilyTag.UNAFFECTED_DAD,
    "tag_unaffected_mom_family": FamilyTag.UNAFFECTED_MOM,
    "tag_unaffected_prb_family": FamilyTag.UNAFFECTED_PRB,
    "tag_unaffected_sib_family": FamilyTag.UNAFFECTED_SIB,
    "tag_male_prb_family": FamilyTag.MALE_PRB,
    "tag_female_prb_family": FamilyTag.FEMALE_PRB,
    "tag_missing_mom_family": FamilyTag.MISSING_MOM,
    "tag_missing_dad_family": FamilyTag.MISSING_DAD,
}


_TAG2LABEL = {
    FamilyTag.NUCLEAR: "tag_nuclear_family",
    FamilyTag.QUAD: "tag_quad_family",
    FamilyTag.TRIO: "tag_trio_family",
    FamilyTag.SIMPLEX: "tag_simplex_family",
    FamilyTag.MULTIPLEX: "tag_multiplex_family",
    FamilyTag.CONTROL: "tag_control_family",
    FamilyTag.AFFECTED_DAD: "tag_affected_dad_family",
    FamilyTag.AFFECTED_MOM: "tag_affected_mom_family",
    FamilyTag.AFFECTED_PRB: "tag_affected_prb_family",
    FamilyTag.AFFECTED_SIB: "tag_affected_sib_family",
    FamilyTag.UNAFFECTED_DAD: "tag_unaffected_dad_family",
    FamilyTag.UNAFFECTED_MOM: "tag_unaffected_mom_family",
    FamilyTag.UNAFFECTED_PRB: "tag_unaffected_prb_family",
    FamilyTag.UNAFFECTED_SIB: "tag_unaffected_sib_family",
    FamilyTag.MALE_PRB: "tag_male_prb_family",
    FamilyTag.FEMALE_PRB: "tag_female_prb_family",
    FamilyTag.MISSING_MOM: "tag_missing_mom_family",
    FamilyTag.MISSING_DAD: "tag_missing_dad_family",
}

ALL_FAMILY_TAGS = set(_TAG2LABEL.keys())
ALL_FAMILY_TAG_LABELS = set(_LABEL2TAG.keys())


class Person:
    """Class to represent an individual."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, **attributes: Any):
        tags = {
            tag: attributes.get(tag.label, False)
            for tag in ALL_FAMILY_TAGS
        }
        self._attributes = {
            key: value
            for key, value in attributes.items()
            if key not in ALL_FAMILY_TAG_LABELS
               and key != "tag_family_type_full"
        }
        self._tags: set[FamilyTag] = set()
        for tag, tag_value in tags.items():
            if isinstance(tag_value, bool) and tag_value:
                self.set_tag(tag)
                continue
            if tag_value == "True":
                self.set_tag(tag)
                continue

            self.unset_tag(tag)
        self.redefine()
        self.is_child: bool = False
        self.is_parent: bool = False

    def redefine(self) -> None:
        # pylint: disable=too-many-branches
        """Extract attributes and turns them into properties."""
        self.family_id: str = self._attributes["family_id"]
        self.person_id: str = self._attributes["person_id"]
        self.fpid: tuple[str, str] = (self.family_id, self.person_id)

        self.sample_id: str = self._attributes.get("sample_id", self.person_id)

        self._sex = Sex.from_name(self._attributes["sex"])
        if "role" not in self._attributes:
            self._role = None
        else:
            self._role = Role.from_name(self._attributes.get("role"))

        self._status = Status.from_name(self._attributes["status"])

        self._attributes["sex"] = self._sex
        self._attributes["role"] = self._role
        self._attributes["status"] = self._status

        self.mom_id: str | None = self.get_attr("mom_id")
        if self.mom_id == "0":
            self.mom_id = None
            self._attributes["mom_id"] = None
        self.dad_id: str | None = self.get_attr("dad_id")
        if self.dad_id == "0":
            self.dad_id = None
            self._attributes["dad_id"] = None
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
        return (
            f"Person({decorator}{self.person_id} ({self.family_id}); "
            f"{self.role}; {self.sex}, {self.status})"
        )

    def to_json(self) -> dict[str, Any]:
        return {
            **self._attributes,
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
    def member_index(self) -> int:
        return int(self._attributes.get("member_index", -1))

    @property
    def role(self) -> Role | None:
        return self._role

    @property
    def sex(self) -> Sex:
        return self._sex

    @property
    def status(self) -> Status:
        return self._status

    @property
    def layout(self) -> str | None:
        return cast(str | None, self._attributes.get("layout", None))

    @property
    def generated(self) -> bool:
        return cast(bool, self._attributes.get("generated", False))

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
    def family_bin(self) -> int | None:
        return cast(int | None, self._attributes.get("family_bin", None))

    @property
    def sample_index(self) -> int | None:
        return cast(int | None, self._attributes.get("sample_index", None))

    def has_attr(self, key: str) -> bool:
        return key in self._attributes

    def get_attr(self, key: str, default: Any = None) -> Any:
        res = self._attributes.get(key, default)
        if isinstance(res, float) and isnan(res):
            return None
        return res

    def set_attr(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def set_tag(self, tag: FamilyTag) -> None:
        self._tags.add(tag)

    def unset_tag(self, tag: FamilyTag) -> None:
        if tag in self._tags:
            self._tags.remove(tag)

    def has_tag(self, tag: FamilyTag) -> bool:
        return tag in self._tags

    def all_tag_labels(self) -> dict[str, bool]:
        return {tag.label: self.has_tag(tag) for tag in ALL_FAMILY_TAGS}

    @property
    def tags(self) -> set[FamilyTag]:
        return self._tags

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

    def diff(self, other: Any) -> list:
        """Collect difference between two individuals."""
        result = []
        if self.family_id != other.family_id:
            result.append(
                f"{self}    family_id: {self.family_id} != {other.family_id}")
        if self.person_id != other.person_id:
            result.append(
                f"{self}    person_id: {self.person_id} != {other.person_id}")
        if self.mom_id != other.mom_id:
            result.append(
                f"{self}       mom_id: {self.mom_id} != {other.mom_id}")
        if self.dad_id != other.dad_id:
            result.append(
                f"{self}       dad_id: {self.dad_id} != {other.dad_id}")
        if self.sex != other.sex:
            result.append(
                f"{self}          sex: {self.sex} != {other.sex}")
        if self.role != other.role:
            result.append(
                f"{self}         role: {self.role} != {other.role}")
        if self.status != other.status:
            result.append(
                f"{self}       status: {self.status} != {other.status}")
        if self.generated != other.generated:
            result.append(
                f"{self}     generated: {self.generated} != {other.generated}")
        if self.not_sequenced != other.not_sequenced:
            result.append(
                f"{self} not_sequenced: "
                f"{self.not_sequenced} != {other.not_sequenced}")
        return result


def get_pedigree_column_names(column_names: set[str]) -> list[str]:
    """Produce pedigree columns given available person or family attributes."""
    columns = [
        col
        for col in PEDIGREE_COLUMN_NAMES.values()
        if col in column_names
    ]
    columns.extend(
        tag_label for tag_label in _LABEL2TAG
    )
    extention_columns = column_names.difference(set(columns))
    extention_columns = extention_columns.difference(
        {"sample_index"},
    )
    columns.extend(sorted(extention_columns))
    return columns


class Family:
    """Defines class to represent a family."""

    def __init__(self, family_id: str):
        self.family_id = family_id
        self.persons: dict[str, Person] = {}
        self._samples_index: tuple[int | None, ...] | None = None
        self._members_in_order: list[Person] | None = None
        self._trios: dict[str, tuple[str, str, str]] | None = None
        self._tags: set[FamilyTag] = set()

    def set_tag(self, tag: FamilyTag) -> None:
        self._tags.add(tag)

    def unset_tag(self, tag: FamilyTag) -> None:
        if tag in self._tags:
            self._tags.remove(tag)

    @property
    def tags(self) -> set[FamilyTag]:
        return self._tags

    @property
    def tag_labels(self) -> set[str]:
        return {tag.label for tag in self._tags}

    def _connect_family(self) -> None:
        index = 0
        for member in self.persons.values():
            if member.missing:
                member.set_attr("member_index", -1)
            else:
                member.set_attr("member_index", index)
                index += 1
            member.is_child = self.member_is_child(member.person_id)
            member.is_parent = self.member_is_parent(member.person_id)

    @staticmethod
    def from_persons(persons: list[Person]) -> Family:
        """Create a family from list of persons."""
        assert len(persons) > 0
        assert all(persons[0].family_id == p.family_id for p in persons)
        family_id = persons[0].family_id

        family = Family(family_id)
        for index, person in enumerate(persons):
            person.set_attr("member_index", index)
            if person.person_id in family.persons:
                raise ValueError(
                    f"multiple person with the same person id "
                    f"{person.person_id} in family {family_id}")
            family.persons[person.person_id] = person
            family._tags |= person.tags  # noqa: SLF001

        # pylint: disable=protected-access
        family._connect_family()  # noqa: SLF001

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
            "family_type": "other",  # deprecated
            "tags": {tag.label for tag in self.tags},
        }

    def get_columns(self) -> list[str]:
        """Collect list of columns for representing a family as data frame."""
        column_names = set(
            self.members_in_order[0]  # noqa: SLF001
                ._attributes.keys())
        return get_pedigree_column_names(column_names)

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
                    lambda m: not m.missing,
                    self.persons.values()),
            )
        return self._members_in_order

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Family):
            return False
        if len(self.persons) != len(other.persons):
            return False
        for person in self.persons.values():
            other_person = other.persons.get(person.person_id)
            if person != other_person:
                return False
        return True

    def has_members(self) -> bool:
        return len(self.members_in_order) > 0

    def member_has_mom(
        self, person_id: str, *,
        allow_missing: bool = False,
    ) -> bool:
        """Check if a member has mom."""
        member = self.persons[person_id]
        if member.mom_id is None or member.mom_id not in self.persons:
            return False
        mom = self.persons[member.mom_id]
        if allow_missing:
            return True
        return not mom.missing

    def member_has_dad(
        self, person_id: str, *,
        allow_missing: bool = False,
    ) -> bool:
        """Check if a member has dad."""
        member = self.persons[person_id]
        if member.dad_id is None or member.dad_id not in self.persons:
            return False
        dad = self.persons[member.dad_id]
        if allow_missing:
            return True
        return not dad.missing

    def member_has_parent(
            self, person_id: str, *,
            allow_missing: bool = False,
    ) -> bool:
        return self.member_has_mom(person_id, allow_missing=allow_missing) or \
            self.member_has_dad(person_id, allow_missing=allow_missing)

    def member_has_both_parents(
        self, person_id: str, *,
        allow_missing: bool = False,
    ) -> bool:
        return self.member_has_mom(person_id, allow_missing=allow_missing) and \
            self.member_has_dad(person_id, allow_missing=allow_missing)

    def member_is_child(self, person_id: str) -> bool:
        member = self.persons[person_id]
        if member.missing:
            return False
        return self.member_has_both_parents(person_id)

    def member_is_parent(self, person_id: str) -> bool:
        member = self.persons[person_id]
        if member.missing:
            return False
        return not self.member_has_dad(person_id) and \
            not self.member_has_mom(person_id)

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
    def samples_index(self) -> tuple[int | None, ...]:
        if self._samples_index is None:
            self._samples_index = tuple(
                m.sample_index for m in self.members_in_order)
        return self._samples_index

    def members_index(
        self, person_ids: Iterable[str],
    ) -> list[int]:
        return [
            self.persons[pid].member_index
            for pid in person_ids]

    def get_member(
        self, person_id: str,
    ) -> Person | None:
        return self.persons.get(person_id, None)

    def get_members_with_roles(
        self, roles: list[str | Role],
    ) -> list[Person]:
        if not isinstance(roles[0], Role):
            assert all(isinstance(role, str) for role in roles)
            roles = [Role.from_name(role) for role in roles]  # type: ignore
        return list(filter(lambda m: m.role in roles, self.members_in_order))

    def get_members_with_statuses(
        self, statuses: list[Status],
    ) -> list[Person]:
        assert all(isinstance(status, Status) for status in statuses)
        return list(
            filter(lambda m: m.status in statuses, self.members_in_order),
        )
