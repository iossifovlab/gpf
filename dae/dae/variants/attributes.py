import enum

_VARIANT_TYPE_DISPLAY_NAME = {
    "invalid": "inv",
    "substitution": "sub",
    "insertion": "ins",
    "deletion": "del",
    "comp": "complex",
    "cnv_p": "cnv+",
    "cnv_m": "cnv-",
}

_ROLE_DISPLAY_NAME = {
    "maternal_grandmother": "Maternal Grandmother",
    "maternal_grandfather": "Maternal Grandfather",
    "paternal_grandmother": "Paternal Grandmother",
    "paternal_grandfather": "Paternal Grandfather",
    "mom": "Mom",
    "dad": "Dad",
    "parent": "Parent",
    "prb": "Proband",
    "sib": "Sibling",
    "child": "Child",
    "maternal_half_sibling": "Maternal Half Sibling",
    "paternal_half_sibling": "Paternal Half Sibling",
    "half_sibling": "Half Sibling",
    "maternal_aunt": "Maternal Aunt",
    "maternal_uncle": "Maternal Uncle",
    "paternal_aunt": "Paternal Aunt",
    "paternal_uncle": "Paternal Uncle",
    "maternal_cousin": "Maternal Cousin",
    "paternal_cousin": "Paternal Cousin",
    "step_mom": "Step Mom",
    "step_dad": "Step Dad",
    "spouse": "Spouse",
    "unknown": "Unknown",
}

_ROLE_SYNONYMS = {
    "maternal grandmother": "maternal_grandmother",
    "maternal grandfather": "maternal_grandfather",
    "paternal grandmother": "paternal_grandmother",
    "paternal grandfather": "paternal_grandfather",
    "mother": "mom",
    "father": "dad",
    "proband": "prb",
    "sibling": "sib",
    "younger sibling": "sib",
    "older sibling": "sib",
    "maternal half sibling": "maternal_half_sibling",
    "paternal half sibling": "paternal_half_sibling",
    "half sibling": "half_sibling",
    "maternal aunt": "maternal_aunt",
    "maternal uncle": "maternal_uncle",
    "paternal aunt": "paternal_aunt",
    "paternal uncle": "paternal_uncle",
    "maternal cousin": "maternal_cousin",
    "paternal cousin": "paternal_cousin",
    "step mom": "step_mom",
    "step dad": "step_dad",
    "step mother": "step_mom",
    "step father": "step_dad",
}


class Role(enum.Enum):

    maternal_grandmother = 1
    maternal_grandfather = 1 << 1
    paternal_grandmother = 1 << 2
    paternal_grandfather = 1 << 3

    mom = 1 << 4
    dad = 1 << 5
    parent = 1 << 6

    prb = 1 << 7
    sib = 1 << 8
    child = 1 << 9

    maternal_half_sibling = 1 << 10
    paternal_half_sibling = 1 << 11
    half_sibling = 1 << 12

    maternal_aunt = 1 << 16
    maternal_uncle = 1 << 17
    paternal_aunt = 1 << 18
    paternal_uncle = 1 << 19

    maternal_cousin = 1 << 20
    paternal_cousin = 1 << 21

    step_mom = 1 << 22
    step_dad = 1 << 23
    spouse = 1 << 24

    unknown = 0

    @property
    def display_name(self):
        return _ROLE_DISPLAY_NAME[self.name]

    def __repr__(self):
        return self.name
        # return "{}: {:023b}".format(self.name, self.value)

    def __str__(self):
        return self.name

    @staticmethod
    def from_name(name):
        if name is None:
            return None
        elif isinstance(name, Role):
            return name
        elif isinstance(name, int):
            return Role.from_value(name)
        elif isinstance(name, str):
            key = name.lower()
            if key in Role.__members__:
                return Role[key]
            if key in _ROLE_SYNONYMS:
                return Role[_ROLE_SYNONYMS[key]]

        return None

    @staticmethod
    def from_value(val):
        return Role(int(val))


class Sex(enum.Enum):
    M = 1
    F = 2
    U = 0

    male = M
    female = F
    unspecified = U

    @staticmethod
    def from_name(name):
        if name is None:
            return Sex.U
        if isinstance(name, Sex):
            return name
        elif isinstance(name, int):
            return Sex.from_value(name)
        assert isinstance(name, str)
        name = name.lower()
        if name in set(["male", "m", "1"]):
            return Sex.male
        elif name in set(["female", "f", "2"]):
            return Sex.female
        elif name in set(["unspecified", "u", "0"]):
            return Sex.unspecified
        raise ValueError("unexpected sex type: " + str(name))

    @staticmethod
    def from_value(val):
        return Sex(int(val))

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def short(self):
        return self.name[0].upper()


class Status(enum.Enum):

    unaffected = 1
    affected = 2
    unspecified = 0

    @staticmethod
    def from_name(name):
        if name is None:
            return Status.unspecified
        elif isinstance(name, Status):
            return name
        elif isinstance(name, int):
            return Status.from_value(name)
        assert isinstance(name, str)
        name = name.lower()
        if name in set(["unaffected", "1", "false"]):
            return Status.unaffected
        elif name in set(["affected", "2", "true"]):
            return Status.affected
        elif name in set(["unspecified", "-", "0"]):
            return Status.unspecified
        raise ValueError("unexpected status type: " + name)

    @staticmethod
    def from_value(val):
        return Status(int(val))

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def short(self):
        return self.name[0].upper()

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Inheritance(enum.Enum):
    reference = 1
    mendelian = 1 << 1
    denovo = 1 << 2
    possible_denovo = 1 << 3
    omission = 1 << 4
    possible_omission = 1 << 5
    other = 1 << 6
    missing = 1 << 7

    unknown = 1 << 8

    @staticmethod
    def from_name(name):
        assert (
            name in Inheritance.__members__
        ), "Inheritance type {} does not exist!".format(name)
        return Inheritance[name]

    @staticmethod
    def from_value(value):
        return Inheritance(value)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class VariantType(enum.Enum):
    invalid = 0
    substitution = 1
    insertion = 1 << 1
    deletion = 1 << 2
    comp = 1 << 3
    cnv_p = 1 << 4
    cnv_m = 1 << 5

    @staticmethod
    def from_name(name):
        name = name.lower().strip()
        if name == "sub" or name == "substitution":
            return VariantType.substitution
        elif name == "ins" or name == "insertion":
            return VariantType.insertion
        elif name == "del" or name == "deletion":
            return VariantType.deletion
        elif name == "comp" or name == "complex":
            return VariantType.comp

        raise ValueError("unexpected variant type: {}".format(name))

    @staticmethod
    def from_name_cnv(name):
        cnv_dup_names = {
            "cnv_p",
            "cnv+",
            "duplication"
        }

        cnv_del_names = {
            "cnv_m",
            "cnv-",
            "deletion"
        }

        name = name.lower().strip()
        if name in cnv_dup_names:
            return VariantType.cnv_p
        elif name in cnv_del_names:
            return VariantType.cnv_m

        raise ValueError("unexpected variant type: {}".format(name))

    @staticmethod
    def from_cshl_variant(variant):
        # FIXME: Change logic to use entire string
        if variant is None:
            return VariantType.invalid

        vt = variant[0:3]
        if vt == "sub":
            return VariantType.substitution
        elif vt == "ins":
            return VariantType.insertion
        elif vt == "del":
            return VariantType.deletion
        elif vt == "com":
            return VariantType.comp
        elif variant == "CNV+":
            return VariantType.cnv_p
        elif variant == "CNV-":
            return VariantType.cnv_m
        else:
            raise ValueError("unexpected variant type: {}".format(variant))

    @staticmethod
    def from_value(value):
        if value is None:
            return None
        return VariantType(value)

    @staticmethod
    def is_cnv(vt):
        return vt == VariantType.cnv_m or vt == VariantType.cnv_p

    def __repr__(self) -> str:
        return _VARIANT_TYPE_DISPLAY_NAME[self.name]

    def __str__(self) -> str:
        return _VARIANT_TYPE_DISPLAY_NAME[self.name]


class GeneticModel(enum.Enum):
    autosomal = 1
    autosomal_broken = 2
    pseudo_autosomal = 3
    X = 4
    X_broken = 5


class TransmissionType(enum.Enum):

    unknown = 0
    transmitted = 1
    denovo = 2
