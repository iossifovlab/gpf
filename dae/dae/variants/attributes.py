import enum

_VARIANT_TYPE_DISPLAY_NAME = {
    "invalid": "inv",
    "substitution": "sub",
    "insertion": "ins",
    "deletion": "del",
    "comp": "comp",
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
    "initially identified proband": "prb",
    "sibling": "sib",
    "younger sibling": "sib",
    "older sibling": "sib",
    "maternal half sibling": "maternal_half_sibling",
    "paternal half sibling": "paternal_half_sibling",
    # "half sibling": "half_sibling",
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
        elif name in set(["unspecified", "u", "0", "unknown"]):
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
        elif name in set(["unspecified", "-", "0", "unknown"]):
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
    indel = insertion | deletion | comp
    cnv_p = 1 << 4
    cnv_m = 1 << 5
    cnv = cnv_p | cnv_m

    tandem_repeat = 1 << 6
    tandem_repeat_ins = tandem_repeat | insertion
    tandem_repeat_del = tandem_repeat | deletion

    def __and__(self, other):
        assert isinstance(other, VariantType), type(other)
        return self.value & other.value

    def __or__(self, other):
        assert isinstance(other, VariantType)
        return self.value | other.value

    def __ior__(self, other):
        assert isinstance(other, VariantType)
        return VariantType(self.value | other.value)

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
        elif name == "cnv_p" or name == "cnv+":
            return VariantType.cnv_p
        elif name == "cnv_m" or name == "cnv-":
            return VariantType.cnv_m
        elif name.lower() in set(["tr", "tandem_repeat"]):
            return VariantType.tandem_repeat

        raise ValueError(f"unexpected variant type: {name}")

    @staticmethod
    def from_cshl_variant(variant):
        # FIXME: Change logic to use entire string
        if variant is None:
            return VariantType.invalid

        vt = variant[0:2]
        if vt == "su":
            return VariantType.substitution
        elif vt == "in":
            return VariantType.insertion
        elif vt == "de":
            return VariantType.deletion
        elif vt == "co":
            return VariantType.comp
        elif vt == "TR":
            return VariantType.tandem_repeat
        elif variant == "CNV+":
            return VariantType.cnv_p
        elif variant == "CNV-":
            return VariantType.cnv_m
        else:
            raise ValueError(f"unexpected variant type: {variant}")

    @staticmethod
    def from_value(value):
        if value is None:
            return None
        return VariantType(value)

    @staticmethod
    def is_cnv(vt):
        if vt is None:
            return False
        assert isinstance(vt, VariantType)
        return vt & VariantType.cnv

    @staticmethod
    def is_tr(vt):
        if vt is None:
            return False
        assert isinstance(vt, VariantType)
        return vt & VariantType.tandem_repeat

    def __repr__(self) -> str:
        return _VARIANT_TYPE_DISPLAY_NAME.get(self.name) or self.name

    def __str__(self) -> str:
        return _VARIANT_TYPE_DISPLAY_NAME.get(self.name) or self.name

    def __lt__(self, other):
        return self.value < other.value


class VariantDesc:

    def __init__(
            self, variant_type, position,
            end_position=None,
            ref=None, alt=None, length=None,
            tr_ref=None, tr_alt=None, tr_unit=None):

        self.variant_type = variant_type
        self.position = position
        self.end_position = end_position

        self.ref = ref
        self.alt = alt
        self.length = length

        self.tr_ref = tr_ref
        self.tr_alt = tr_alt
        self.tr_unit = tr_unit

    def __repr__(self):
        return self.to_cshl_short()

    def to_cshl_short(self):

        if self.variant_type & VariantType.substitution:
            return f"sub({self.ref}->{self.alt})"
        elif self.variant_type & VariantType.insertion:
            return f"ins({self.alt})"
        elif self.variant_type & VariantType.deletion:
            return f"del({self.length})"
        elif self.variant_type & VariantType.comp:
            return f"comp({self.ref}->{self.alt})"
        elif self.variant_type & VariantType.cnv_p:
            return "CNV+"
        elif self.variant_type & VariantType.cnv_m:
            return "CNV-"

    def to_cshl_full(self):

        if self.variant_type & VariantType.tandem_repeat:
            return f"TR({self.tr_ref}x{self.tr_unit}->{self.tr_alt})"
        elif self.variant_type & VariantType.substitution:
            return f"sub({self.ref}->{self.alt})"
        elif self.variant_type & VariantType.insertion:
            return f"ins({self.alt})"
        elif self.variant_type & VariantType.deletion:
            return f"del({self.length})"
        elif self.variant_type & VariantType.comp:
            return f"comp({self.ref}->{self.alt})"
        elif self.variant_type & VariantType.cnv_p:
            return "CNV+"
        elif self.variant_type & VariantType.cnv_m:
            return "CNV-"

    @staticmethod
    def combine(variant_descs):
        if all([variant_descs[0].variant_type == vd.variant_type
                for vd in variant_descs]) or \
            all([
                vd.variant_type & VariantType.tandem_repeat
                for vd in variant_descs]):

            result = VariantDesc(
                variant_descs[0].variant_type,
                variant_descs[0].position,
                ref=variant_descs[0].ref,
                alt=",".join(filter(
                    lambda a: a is not None,
                    [vd.alt for vd in variant_descs])),
                length=variant_descs[-1].length,
                tr_ref=variant_descs[0].tr_ref,
                tr_alt=",".join(filter(
                    lambda a: a is not None,
                    [str(vd.tr_alt) for vd in variant_descs])),
                tr_unit=variant_descs[0].tr_unit
            )
            return [result.to_cshl_full()]
        return [str(vd) for vd in variant_descs]


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
