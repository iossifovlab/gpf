from dae.pedigrees.family import FamilyType, Person


class RemoteFamily:
    def __init__(self, json):
        self._family_id = json["family_id"]
        self._person_ids = json["person_ids"]
        self._samples_index = json["samples_index"]
        self._family_type = FamilyType.from_name(json["family_type"])
        self.persons = {pid: None for pid in self._person_ids}

    def add_members(self, persons):
        assert all([isinstance(p, RemotePerson) for p in persons])
        assert all([p.family_id == self.family_id for p in persons])

        for p in persons:
            self.persons[p.person_id] = p
        self._connect_family()

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

    def get_member(self, member_id):
        return self.persons.get(member_id, None)

    @property
    def family_id(self):
        return self._family_id

    @property
    def samples_index(self):
        return self._samples_index

    @property
    def members_ids(self):
        return self._person_ids

    @property
    def family_type(self):
        return self._family_type


class RemotePerson:
    def __init__(self, json):
        self.person_id = json["person_id"]
        self.dad_id = json["dad_id"]
        self.mom_id = json["mom_id"]
        self._sample_id = json["sample_id"]
        self._index = json["index"]
        self._sex = json["sex"]
        self._role = json["role"]
        self._status = json["status"]
        self._layout = json["layout"]
        self._generated = json["generated"]
        self._family_bin = json["family_bin"]
        self._not_sequenced = json["not_sequenced"]
        self._missing = json["missing"]

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
        return self._layout

    @property
    def generated(self):
        return self._generated

    @property
    def not_sequenced(self):
        return self.generated or \
            self._not_sequenced

    @property
    def missing(self):
        return self.generated or self.not_sequenced or\
            self._missing

    @property
    def family_bin(self):
        return self._family_bin

    @property
    def sample_index(self):
        return self._sample_index

    def has_mom(self):
        return self.mom is not None

    def has_dad(self):
        return self.dad is not None

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def has_both_parents(self):
        return self.has_dad() and self.has_mom()

    def __eq__(self, other):
        if not isinstance(other, RemotePerson) and \
                not isinstance(other, Person):
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

    def __repr__(self):
        decorator = ""
        if self.generated:
            decorator = "[G] "
        elif self.not_sequenced:
            decorator = "[N] "
        return f"RemotePerson({decorator}{self.person_id}" \
            f"({self.family_id}); {self.role}; {self.sex}, {self.status})"

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
