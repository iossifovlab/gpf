'''
Created on Feb 13, 2018

@author: lubo
'''
import enum


class Role(enum.Enum):

    DISPLAY_NAME = {
        'maternal_grandmother': 'Maternal Grandmother',
        'maternal_grandfather': 'Maternal Grandfather',
        'paternal_grandmother': 'Paternal Grandmother',
        'paternal_grandfather': 'Paternal Grandfather',

        'mom': 'Mom',
        'dad': 'Dad',
        'parent': 'Parent',

        'prb': 'Proband',
        'sib': 'Sibling',
        'child': 'Child',

        'maternal_half_sibling': 'Maternal Half Sibling',
        'paternal_half_sibling': 'Paternal Half Sibling',
        'half_sibling': 'Half Sibling',

        'maternal_aunt': 'Maternal Aunt',
        'maternal_uncle': 'Maternal Uncle',
        'paternal_aunt': 'Paternal Aunt',
        'paternal_uncle': 'Paternal Uncle',

        'maternal_cousin': 'Maternal Cousin',
        'paternal_cousin': 'Paternal Cousin',

        'step_mom': 'Step Mom',
        'step_dad': 'Step Dad',
        'spouse': 'Spouse',

        'unknown': 'Unknown'
    }

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
        return Role.DISPLAY_NAME.value[self.name]

    def __repr__(self):
        return self.name
        # return "{}: {:023b}".format(self.name, self.value)

    def __str__(self):
        return self.name

    @staticmethod
    def from_name(name):
        assert name is not None
        if isinstance(name, Role):
            return name
        elif name in Role.__members__:
            return Role[name]
        else:
            print(f"Role '{name}' is unknown")
            return Role.unknown

    @staticmethod
    def from_value(val):
        return Role(int(val))

    @classmethod
    def from_name_or_value(cls, name_or_value):
        try:
            return cls.from_name(name_or_value)
        except ValueError:
            return cls.from_value(name_or_value)

    @staticmethod
    def from_display_name(display_name):
        if display_name in Role.DISPLAY_NAME.value.values():
            for name, display_name_value in Role.DISPLAY_NAME.value.items():
                if display_name_value == display_name:
                    return Role.from_name(name)
            return Role.unknown
        else:
            return Role.unknown


class Sex(enum.Enum):
    M = 1
    F = 2
    U = 0

    male = M
    female = F
    unspecified = U

    @staticmethod
    def from_name(name):
        if isinstance(name, Sex):
            return name
        elif name == 'male' or name == 'M' or name == '1':
            return Sex.male
        elif name == 'female' or name == 'F' or name == '2':
            return Sex.female
        elif name == 'unspecified' or name == 'U' or name == '0':
            return Sex.unspecified
        raise ValueError("unexpected sex type: " + str(name))

    @staticmethod
    def from_value(val):
        return Sex(int(val))

    @classmethod
    def from_name_or_value(cls, name_or_value):
        try:
            return cls.from_name(name_or_value)
        except ValueError:
            return cls.from_value(name_or_value)

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
        if isinstance(name, Status):
            return name
        elif name == 'unaffected' or name == '1':
            return Status.unaffected
        elif name == 'affected' or name == '2':
            return Status.affected
        elif name == 'unspecified' or name == '-' or name == '0':
            return Status.unspecified
        raise ValueError("unexpected status type: " + name)

    @staticmethod
    def from_value(val):
        return Status(int(val))

    @classmethod
    def from_name_or_value(cls, name_or_value):
        try:
            return cls.from_name(name_or_value)
        except ValueError:
            return cls.from_value(name_or_value)

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
    other = 1 << 5
    missing = 1 << 6
    unknown = 1 << 7

    MASK = 127

    @staticmethod
    def from_name(name):
        assert name in Inheritance.__members__, \
            'Inheritance type {} does not exist!'.format(name)
        return Inheritance[name]

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class VariantType(enum.Enum):
    invalid = 0
    substitution = 1
    insertion = 1 << 1
    deletion = 1 << 2
    complex = 1 << 3
    CNV = 1 << 4

    @staticmethod
    def from_name(name):
        if name == 'sub' or name == 'substitution':
            return VariantType.substitution
        elif name == 'ins' or name == 'insertion':
            return VariantType.insertion
        elif name == 'del' or name == 'deletion':
            return VariantType.deletion
        elif name == 'complex':
            return VariantType.complex
        elif name == 'CNV':
            return VariantType.CNV
        raise ValueError("unexpected variant type: {}".format(name))

    @staticmethod
    def from_cshl_variant(variant):
        if variant is None:
            return VariantType.none

        vt = variant[0]
        if vt == 's':
            return VariantType.substitution
        elif vt == 'i':
            return VariantType.insertion
        elif vt == 'd':
            return VariantType.deletion
        elif vt == 'c':
            return VariantType.complex
        elif vt == 'C':
            return VariantType.CNV
        else:
            raise ValueError("unexpected variant type: {}".format(variant))

    def __repr__(self):
        return self.name[:3]

    def __str__(self):
        return self.name[:3]


class GeneticModel(enum.Enum):
    autosomal = 1
    pseudo_autosomal = 2
    X = 3
    X_broken = 4
