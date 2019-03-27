'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

import enum


class Role(enum.Enum):

    maternal_grandmother = 1
    maternal_grandfather = 2
    paternal_grandmother = 3
    paternal_grandfather = 4

    mom = 10
    dad = 11
    parent = 12

    prb = 20
    sib = 21
    child = 22

    maternal_half_sibling = 30
    paternal_half_sibling = 31
    half_sibling = 32

    maternal_aunt = 50
    maternal_uncle = 51
    paternal_aunt = 52
    paternal_uncle = 53

    maternal_cousin = 60
    paternal_cousin = 61

    step_mom = 70
    step_dad = 71
    spouse = 72

    unknown = 100

    def __repr__(self):
        return self.name
        # return "{}: {:023b}".format(self.name, self.value)

    def __str__(self):
        return self.name

    @staticmethod
    def from_name(name):
        if name in Role.__members__:
            return Role[name]
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
        if name == 'male' or name == 'M' or name == '1':
            return Sex.male
        elif name == 'female' or name == 'F' or name == '2':
            return Sex.female
        elif name == 'unspecified' or name == 'U' or name == '0':
            return Sex.unspecified
        raise ValueError("unexpected sex type: " + name)

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
        if name == 'unaffected' or name == '1':
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
    mendelian = 2
    denovo = 4
    possible_denovo = 5
    omission = 8
    other = 16
    missing = 32
    unknown = 64

    @staticmethod
    def from_name(name):
        assert name in Inheritance.__members__
        return Inheritance[name]

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class VariantType(enum.Enum):
    invalid = 0
    substitution = 1
    insertion = 2
    deletion = 3
    complex = 4
    CNV = 5

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
