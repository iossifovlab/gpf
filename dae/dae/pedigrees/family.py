from __future__ import annotations

import copy
import logging

from typing import Dict, Iterator, Optional, Set, List
from enum import Enum, auto
from collections import defaultdict
from collections.abc import Mapping
from dae.utils.helpers import isnan

import pandas as pd

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
}


class FamilyType(Enum):
    TRIO = auto()
    QUAD = auto()
    MULTIGENERATIONAL = auto()
    SIMPLEX = auto()
    MULTIPLEX = auto()
    OTHER = auto()

    @staticmethod
    def from_name(name: str):
        assert isinstance(name, str)
        name = name.lower()
        if name == "trio":
            return FamilyType.TRIO
        elif name == "quad":
            return FamilyType.QUAD
        elif name == "multigenerational":
            return FamilyType.MULTIGENERATIONAL
        elif name == "simplex":
            return FamilyType.SIMPLEX
        elif name == "multiplex":
            return FamilyType.MULTIPLEX
        elif name == "other":
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


class Person(object):
    def __init__(self, **attributes):
        self._attributes = attributes
        self.redefine()

    def redefine(self):
        assert "person_id" in self._attributes
        self.family_id = self._attributes["family_id"]
        self.family = None
        self.person_id = self._attributes["person_id"]
        self.sample_id = self._attributes.get("sample_id", None)
        self.index = self._attributes.get("index", None)

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
        self.mom = None
        self.dad = None
        assert self.mom_id is None or type(self.mom_id) == str, \
            (self, self._attributes)
        assert self.dad_id is None or type(self.dad_id) == str, \
            (self, self._attributes)
        if self._attributes.get("not_sequenced"):
            value = self._attributes.get("not_sequenced")
            if value == "None" or value == "0" or value == "False":
                self._attributes["not_sequenced"] = None
        if self._attributes.get("generated"):
            value = self._attributes.get("generated")
            if value == "None" or value == "0" or value == "False":
                self._attributes["generated"] = None

    def __repr__(self):
        decorator = ""
        if self.generated:
            decorator = "[G] "
        elif self.not_sequenced:
            decorator = "[N] "
        return f"Person({decorator}{self.person_id} ({self.family_id}); " \
            f"{self.role}; {self.sex}, {self.status})"

    def to_json(self):
        return {
            "family_id": self.family_id,
            "person_id": self.person_id,
            "dad_id": self.dad_id,
            "mom_id": self.mom_id,
            "sample_id": self.sample_id,
            "index": self.index,
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
    def role(self):
        return self._role

    @property
    def sex(self):
        return self._sex

    @property
    def status(self):
        return self._status

    @property
    def layout(self):
        return self._attributes.get("layout", None)

    @property
    def generated(self):
        return self._attributes.get("generated", None)

    @property
    def not_sequenced(self):
        return self.generated or \
            self._attributes.get("not_sequenced", None)

    @property
    def missing(self):
        return self.generated or self.not_sequenced or\
            self._attributes.get("missing", False)

    @property
    def family_bin(self):
        return self._attributes.get("family_bin", None)

    @property
    def sample_index(self):
        return self._attributes.get("sample_index", None)

    def has_mom(self):
        return self.mom is not None

    def has_dad(self):
        return self.dad is not None

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def has_both_parents(self):
        return self.has_dad() and self.has_mom()

    def has_missing_parent(self):
        return \
            (self.has_dad() and
             (self.dad.generated or self.dad.not_sequenced)) or \
            (self.has_mom() and
             (self.mom.generated or self.mom.not_sequenced))

    def has_attr(self, key):
        return key in self._attributes

    def get_attr(self, key, default=None):
        res = self._attributes.get(key, default)
        if type(res) == float and isnan(res):
            return None
        return res

    def set_attr(self, key, value):
        self._attributes[key] = value

    def __eq__(self, other):
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

    def diff(self, other):
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


class Family(object):
    def __init__(self, family_id):
        self.family_id = family_id
        self.persons = {}
        self._samples_index = None
        self._members_in_order = None
        self._trios = None

    def _connect_family(self):
        index = 0
        for member in self.persons.values():
            member.family = self
            member.mom = self.get_member(member.mom_id, None)
            member.dad = self.get_member(member.dad_id, None)
            if member.missing:
                member.index = -1
            else:
                member.index = index
                index += 1

    @staticmethod
    def from_persons(persons) -> "Family":
        assert len(persons) > 0
        assert all([persons[0].family_id == p.family_id for p in persons])
        family_id = persons[0].family_id
        # persons = sorted(
        #     persons, key=lambda p: p.role.value if p.role else -1)

        family = Family(family_id)
        for index, person in enumerate(persons):
            person.set_attr("member_index", index)
            family.persons[person.person_id] = person
        family._connect_family()
        assert all([p.family is not None for p in family.persons.values()])

        return family

    @staticmethod
    def from_records(records):
        persons = []
        for rec in records:
            person = Person(**rec)
            persons.append(person)
        return Family.from_persons(persons)

    def __len__(self):
        return len(self.members_in_order)

    def __repr__(self):
        return f"Family({self.family_id}, {list(self.persons.values())})"

    def to_json(self):
        return {
            "family_id": self.family_id,
            "person_ids": self.members_ids,
            "samples_index": self._samples_index,
            "family_type": self.family_type.name
        }

    def add_members(self, persons):
        assert all([isinstance(p, Person) for p in persons])
        assert all([p.family_id == self.family_id for p in persons])

        for index, p in enumerate(persons):
            self.persons[p.person_id] = p
        self.redefine()

    def redefine(self):
        self._members_in_order = None
        self._trios = None
        self._samples_index = None
        self._connect_family()

    @property
    def full_members(self):
        return list(self.persons.values())

    @property
    def members_in_order(self):
        if self._members_in_order is None:
            self._members_in_order = list(
                filter(
                    lambda m: not m.missing,
                    self.persons.values())
            )
        return self._members_in_order

    def __eq__(self, other):
        if len(self.full_members) != len(other.full_members):
            return False
        for m1, m2 in zip(self.full_members, other.full_members):
            if m1 != m2:
                return False
        return True

    def has_members(self):
        return len(self.members_in_order) > 0

    @property
    def members_ids(self):
        return [m.person_id for m in self.members_in_order]

    @property
    def trios(self):
        if self._trios is None:
            self._trios = {}
            members = {m.person_id: m for m in self.members_in_order}
            for pid, p in list(members.items()):
                if p.mom_id in members and p.dad_id in members:
                    self._trios[pid] = [pid, p.mom_id, p.dad_id]
        return self._trios

    @property
    def samples_index(self):
        if self._samples_index is None:
            self._samples_index = tuple(
                [m.sample_index for m in self.members_in_order]
            )
        return self._samples_index

    @property
    def family_type(self):
        has_grandparent = any([
            person.role in (
                Role.maternal_grandfather,
                Role.maternal_grandmother,
                Role.paternal_grandfather,
                Role.paternal_grandmother
            ) for person in self.persons.values()
        ])

        unaffected_parents = all([
            person.status is Status.unaffected
            for person in self.get_members_with_roles([Role.mom, Role.dad])
        ])

        affected_siblings = any([
            person.status is Status.affected
            for person in self.get_members_with_roles([Role.sib])
        ])

        if has_grandparent:
            return FamilyType.MULTIGENERATIONAL
        if unaffected_parents:
            if len(self.persons) == 3:
                return FamilyType.TRIO
            elif len(self.persons) == 4 and not affected_siblings:
                return FamilyType.QUAD
            elif affected_siblings:
                return FamilyType.MULTIPLEX
        else:
            if affected_siblings:
                return FamilyType.MULTIPLEX
            else:
                return FamilyType.SIMPLEX
        return FamilyType.OTHER

    @staticmethod
    def merge(l_fam: "Family", r_fam: "Family", forced=True) -> "Family":
        assert l_fam.family_id == r_fam.family_id, \
            ("Merging families is only allowed with matching family IDs!"
             f" ({l_fam.family_id} != {r_fam.family_id})")

        people_intersection = \
            set(l_fam.persons.keys()) & set(r_fam.persons.keys())

        merged_persons = dict()
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

            match = (l_person.sex == r_person.sex or
                     l_person.sex == Sex.unspecified or
                     r_person.sex == Sex.unspecified) and \
                    (l_person.status == r_person.status or
                     l_person.status == Status.unspecified or
                     r_person.status == Status.unspecified) and \
                    (l_person.role == r_person.role or
                     l_person.role == Role.unknown or
                     r_person.role == Role.unknown) and \
                    (l_person.family_id == r_person.family_id)
            if not match:
                message = f"mismatched attributes for person {person_id}; " \
                    f"sex[{l_person.sex} == {r_person.sex}], " \
                    f"status[{l_person.status} == {r_person.status}], " \
                    f"role[{l_person.role} == {r_person.role}], " \
                    f"family[{l_person.family_id} == {r_person.family_id}]"

                logger.warning(message)
                if forced:
                    logger.warning(f"second person overwrites: {r_person}")
                    merged_persons[person_id] = r_person
                else:
                    raise AssertionError(message)

        # Construct new instances of Person to avoid
        # modifying the original family's Person instances
        return Family.from_persons([
            Person(**person._attributes)
            for person in merged_persons.values()
        ])

    def members_index(self, person_ids):
        index = []
        for pid in person_ids:
            index.append(self.persons[pid].index)
        return index

    def get_member(self, person_id, default=None):
        return self.persons.get(person_id, default)

    def get_members_with_roles(self, roles):
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        return list(filter(lambda m: m.role in roles, self.members_in_order))

    def get_members_with_statuses(self, statuses):
        if not isinstance(statuses[0], Status):
            statuses = [Status.from_name(status) for status in statuses]
        return list(
            filter(lambda m: m.status in statuses, self.members_in_order)
        )


class FamiliesData(Mapping):
    def __init__(self):
        self._ped_df: Optional[pd.DataFrame] = None
        self._families: Dict[str, Family] = {}
        self.persons = {}
        self._broken = {}
        self._person_ids_with_parents = None
        self._real_persons = None
        self._families_by_type: Dict[str, Set[str]] = {}

    def redefine(self):
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
                        f"person {person.person_id} included in more "
                        f"than one family: {family.family_id}, "
                        f"{self.persons[person.person_id].family_id}")
                    error_msgs.append(
                        f"person {person.person_id} "
                        f"in multiple families")
                self.persons[person.person_id] = person
        if error_msgs:
            raise AttributeError("; ".join(error_msgs))

    @property
    def broken_families(self):
        return self._broken

    @property
    def real_persons(self):
        if self._real_persons is None:
            self._real_persons = {}
            for p in self.persons.values():
                if not p.generated:
                    self._real_persons[p.person_id] = p
        return self._real_persons

    @property
    def families_by_type(self):
        if not self._families_by_type:
            for family_id, family in self._families.items():
                self._families_by_type.setdefault(
                    family.family_type, set()
                ).add(family_id)
        return self._families_by_type

    @staticmethod
    def from_family_persons(
            family_persons: Dict[str, List[Person]]) -> FamiliesData:
        families_data = FamiliesData()
        for family_id, persons in family_persons.items():
            assert all([isinstance(p, Person) for p in persons]), persons

            family = Family.from_persons(persons)
            families_data._families[family_id] = family
            for person_id, person in family.persons.items():
                families_data.persons[person_id] = person
        return families_data

    @staticmethod
    def from_pedigree_df(ped_df: pd.DataFrame) -> FamiliesData:
        persons = defaultdict(list)
        for rec in ped_df.to_dict(orient="records"):
            person = Person(**rec)
            persons[person.family_id].append(person)

        fams = FamiliesData.from_family_persons(persons)
        return fams

    @staticmethod
    def from_families(families: Dict[str, Family]) -> FamiliesData:
        return FamiliesData.from_family_persons(
            {fam.family_id: fam.full_members for fam in families.values()}
        )

    def pedigree_samples(self):
        result = []
        for family in self.values():
            for member in family.members_in_order:
                result.append(member.sample_id)
        return result

    @property
    def ped_df(self) -> pd.DataFrame:
        if self._ped_df is None:
            # build ped_df
            column_names: Set[str] = set()
            records = []
            for family in self.values():
                for person in family.full_members:
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
        return FamiliesData.from_pedigree_df(self.ped_df)

    def __getitem__(self, family_id) -> Family:
        return self._families[family_id]

    def __len__(self) -> int:
        return len(self._families)

    def __iter__(self) -> Iterator[str]:
        return iter(self._families.keys())

    def __contains__(self, family_id) -> bool:
        return family_id in self._families

    def __delitem__(self, family_id) -> None:
        del self._families[family_id]

    def keys(self):
        return self._families.keys()

    def values(self):
        return self._families.values()

    def items(self):
        return self._families.items()

    def get(self, family_id, default=None) -> Optional[Family]:
        return self._families.get(family_id, default)

    def families_query_by_person_ids(self, person_ids):
        res = {}
        for person_id in person_ids:
            person = self.persons.get(person_id)
            if person is None:
                continue
            if person.family_id in res:
                continue
            family = self._families[person.family_id]
            res[family.family_id] = family
        return res

    def persons_without_parents(self):
        person = []
        for fam in list(self._families.values()):
            for p in fam.members_in_order:
                if not p.has_parent():
                    person.append(p)
        return person

    def persons_with_parents(self):
        person = []
        for fam in list(self._families.values()):
            for p in fam.members_in_order:
                if p.has_both_parents() and (not p.has_missing_parent()):
                    person.append(p)
        return person

    def person_ids_with_parents(self):
        if self._person_ids_with_parents is None:
            self._person_ids_with_parents = set()
            for fam in list(self._families.values()):
                for p in fam.members_in_order:
                    if p.has_both_parents() and (not p.has_missing_parent()):
                        self._person_ids_with_parents.add(p.person_id)
        return self._person_ids_with_parents

    def persons_with_roles(self, roles=None, family_ids=None):
        if family_ids is None:
            persons = self.persons.values()
        else:
            family_ids = set(family_ids)
            persons = filter(
                lambda p: p.family_id in family_ids,
                self.persons.values())

        if roles is None:
            return persons

        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]

        return list(filter(lambda m: m.role in roles, persons))

    def families_of_persons(self, person_ids: Set[str]) -> Set[str]:
        family_ids: Set[str] = set()
        for person_id in person_ids:
            family_ids.add(self.persons[person_id].family_id)
        return family_ids

    @staticmethod
    def combine(
            first: FamiliesData, second: FamiliesData,
            forced=True) -> FamiliesData:

        same_families = set(first.keys()) & \
            set(second.keys())
        combined_dict: Dict[str, Family] = {}
        combined_dict.update(first)
        combined_dict.update(second)
        mismatched_families = []
        for sf in same_families:
            try:
                combined_dict[sf] = Family.merge(
                    first[sf], second[sf], forced=forced)
            except AssertionError as ex:
                import traceback
                traceback.print_exc()
                logger.error(f"mismatched families: {first[sf]}, {second[sf]}")
                logger.exception(ex)

                mismatched_families.append(sf)

        if len(mismatched_families) > 0:
            logger.warning(f"mismatched families: {mismatched_families}")
            if not forced:
                assert len(mismatched_families) == 0, mismatched_families
            else:
                logger.warning("second family overwrites family definition")

        return FamiliesData.from_families(combined_dict)

    @staticmethod
    def combine_studies(studies, forced=True) -> FamiliesData:
        assert len(studies) > 0, studies

        logger.info(
            f"building combined families from studies: "
            f"{[st.id for st in studies]}")

        if len(studies) == 1:
            return FamiliesData.copy(studies[0].families)

        logger.info(
            f"combining families from study {studies[0].id} "
            f"and from study {studies[1].id}")
        result = FamiliesData.combine(
            studies[0].families,
            studies[1].families)

        if len(studies) > 2:
            for si in range(2, len(studies)):
                logger.debug(
                    f"processing study ({si}): "
                    f"{studies[si].id}")
                logger.info(
                    f"combining families from studies ({si}) "
                    f"{[st.study_id for st in studies[:si]]} "
                    f"with families from study "
                    f"{studies[si].id}")
                result = FamiliesData.combine(
                    result,
                    studies[si].families
                )

        return result
