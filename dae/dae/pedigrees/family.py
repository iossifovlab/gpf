import copy

from collections import defaultdict
from collections.abc import Mapping

import pandas as pd

from dae.variants.attributes import Role, Sex, Status


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
}


class Person(object):
    def __init__(self, **attributes):
        self._attributes = attributes

        assert "person_id" in attributes
        self.family_id = attributes["family_id"]
        self.family = None
        self.person_id = attributes["person_id"]
        self.sample_id = attributes.get("sample_id", None)
        self.index = attributes.get("index", None)

        self._sex = Sex.from_name(attributes["sex"])
        if "role" not in attributes:
            self._role = None
        else:
            self._role = Role.from_name(attributes.get("role"))

        self._status = Status.from_name(attributes["status"])

        self._attributes["sex"] = self._sex
        self._attributes["role"] = self._role
        self._attributes["status"] = self._status

        self.mom_id = attributes.get("mom_id", None)
        if self.mom_id == "0":
            self.mom_id = None
            self._attributes["mom_id"] = None
        self.dad_id = attributes.get("dad_id", None)
        if self.dad_id == "0":
            self.dad_id = None
            self._attributes["dad_id"] = None
        self.mom = None
        self.dad = None

    def __repr__(self):
        if self.generated:
            return "Person([G] {} ({}); {}; {})".format(
                self.person_id, self.family_id, self.role, self.sex
            )
        return "Person({} ({}); {}; {})".format(
            self.person_id, self.family_id, self.role, self.sex
        )

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

    def has_generated_parent(self):
        return (self.has_dad() and self.dad.generated) or (
            self.has_mom() and self.mom.generated
        )

    def has_attr(self, key):
        return key in self._attributes

    def get_attr(self, key, default=None):
        return self._attributes.get(key, default)

    def set_attr(self, key, value):
        self._attributes[key] = value


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
            if member.generated:
                member.index = -1
            else:
                member.index = index
                index += 1

    @staticmethod
    def from_persons(persons) -> "Family":
        assert len(persons) > 0
        assert all([persons[0].family_id == p.family_id for p in persons])
        family_id = persons[0].family_id

        family = Family(family_id)
        for person in persons:
            family.persons[person.person_id] = person
        family._connect_family()
        assert all([p.family is not None for p in family.persons.values()])

        return family

    def __len__(self):
        return len(self.members_in_order)

    def __repr__(self):
        return f"Family({self.family_id}, {list(self.persons.values())})"

    def add_members(self, persons):
        assert all([isinstance(p, Person) for p in persons])
        assert all([p.family_id == self.family_id for p in persons])

        for p in persons:
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
                filter(lambda m: not m.generated, self.persons.values())
            )
        return self._members_in_order

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

    @staticmethod
    def merge(l_fam: "Family", r_fam: "Family") -> "Family":
        assert l_fam.family_id == r_fam.family_id, \
            (f"Merging families is only allowed with matching family IDs!"
             " ({l_fam.family_id} != {r_fam.family_id})")

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

            assert (l_person.sex == r_person.sex or \
                    l_person.sex == Sex.unspecified or \
                    r_person.sex == Sex.unspecified) \
                and (l_person.role == r_person.role) \
                and (l_person.family_id == r_person.family_id), \
                f"Mismatched attributes for person {person_id}; " \
                f"{l_person.sex} == {r_person.sex}, " \
                f"{l_person.role} == {r_person.role}, " \
                f"{l_person.family_id} == {r_person.family_id}"

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
        self._ped_df = None
        self._families = {}
        self.persons = {}
        self._broken = {}

    def redefine(self):
        self.persons = {}
        self._ped_df = None

        all_families = self._families.values()
        self._families = {}
        for family in all_families:
            family.redefine()

            if len(family) == 0:
                self._broken[family.family_id] = family
            else:
                self._families[family.family_id] = family

            for person in family.full_members:
                self.persons[person.person_id] = person

    @staticmethod
    def from_family_persons(family_persons):
        families_data = FamiliesData()
        for family_id, persons in family_persons:
            assert all([isinstance(p, Person) for p in persons]), persons

            family = Family.from_persons(persons)
            families_data._families[family_id] = family
            for person_id, person in family.persons.items():
                families_data.persons[person_id] = person
        return families_data

    @staticmethod
    def from_pedigree_df(ped_df):
        persons = defaultdict(list)
        for rec in ped_df.to_dict(orient="record"):
            person = Person(**rec)
            persons[person.family_id].append(person)

        fams = FamiliesData.from_family_persons(
            [
                (family_id, family_persons)
                for family_id, family_persons in persons.items()
            ]
        )
        return fams

    @staticmethod
    def from_families(families):
        return FamiliesData.from_family_persons(
            [(fam.family_id, fam.full_members) for fam in families.values()]
        )

    @property
    def ped_df(self):
        if self._ped_df is None:
            # build ped_df
            column_names = set()
            records = []
            for family in self.values():
                for person in family.full_members:
                    rec = copy.deepcopy(person._attributes)
                    rec["mom_id"] = person.mom_id if person.mom_id else "0"
                    rec["dad_id"] = person.dad_id if person.dad_id else "0"
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

    def __getitem__(self, family_id):
        return self._families[family_id]

    def __len__(self):
        return len(self._families)

    def __iter__(self):
        return iter(self._families)

    def __contains__(self, family_id):
        return family_id in self._families

    def keys(self):
        return self._families.keys()

    def values(self):
        return self._families.values()

    def items(self):
        return self._families.items()

    def get(self, family_id, default=None):
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
                if p.has_both_parents() and (not p.has_generated_parent()):
                    person.append(p)
        return person

    def persons_with_roles(self, roles, family_ids=None):
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        if family_ids is None:
            persons = self.persons.values()
        else:
            family_ids = set(family_ids)
            persons = filter(
                lambda p: p.family_id in family_ids,
                self.persons.values())
        return list(filter(lambda m: m.role in roles, persons))
