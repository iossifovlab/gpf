from __future__ import annotations

import enum
import logging
from typing import Any

logger = logging.getLogger(__name__)

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
    """Enumerator for a person's role in a pedigree."""

    # pylint: disable=invalid-name
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

    unknown = 1 << 25

    @property
    def display_name(self) -> str:
        return _ROLE_DISPLAY_NAME[self.name]

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_name(name: str | int | None) -> Role:
        """Construct and return a Role from it's string representation."""
        if isinstance(name, Role):
            return name
        if isinstance(name, int):
            return Role.from_value(name)
        if isinstance(name, str):
            key = name.lower()
            if key in Role.__members__:
                return Role[key]
            if key in _ROLE_SYNONYMS:
                return Role[_ROLE_SYNONYMS[key]]

        logger.debug("unexpected role name: <%s>", name)
        return Role.unknown

    @staticmethod
    def to_value(name: str | int | None) -> int:
        role = Role.from_name(name)
        return role.value

    @staticmethod
    def to_name(value: int) -> str:
        return Role(value).name

    @staticmethod
    def from_value(val: int) -> Role:
        val = int(val)
        if val == 0:
            return Role.unknown
        return Role(val)

    @staticmethod
    def not_role(value: int) -> int:
        return (1 << 24) - 1 - value


class Sex(enum.Enum):
    """Enumerator for a person's sex."""

    M = 1
    F = 2
    U = 4

    # pylint: disable=invalid-name
    male = M
    female = F
    unspecified = U

    @staticmethod
    def aliases() -> dict[str, str]:
        return {
            "M": "male",
            "F": "female",
            "U": "unspecified",
        }

    @staticmethod
    def from_name(name: int | str | None) -> Sex:
        """Construct and return person Sex from string."""
        if name is None:
            return Sex.U
        if isinstance(name, Sex):
            return name
        if isinstance(name, int):
            return Sex.from_value(name)
        assert isinstance(name, str)
        name = name.lower()
        if name in {"male", "m", "1"}:
            return Sex.male
        if name in {"female", "f", "2"}:
            return Sex.female
        if name in {"unspecified", "u", "0", "unknown"}:
            return Sex.unspecified
        raise ValueError(f"unexpected sex name: {name}")

    @staticmethod
    def _internal_value(value: int) -> int:
        return 4 if value == 0 else value

    @staticmethod
    def _external_value(value: int) -> int:
        return 0 if value == 4 else value

    @staticmethod
    def to_value(name: int | str | None) -> int:
        sex = Sex.from_name(name)
        return Sex._external_value(sex.value)

    @staticmethod
    def to_name(value: int) -> str:
        return Sex(Sex._internal_value(value)).name

    @staticmethod
    def from_value(val: int) -> Sex:
        return Sex(Sex._internal_value(int(val)))

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    def short(self) -> str:
        return self.name[0].upper()

    def __lt__(self, other: Sex) -> bool:
        return bool(self.value < other.value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Sex):
            return False
        return bool(self.value == other.value)

    def __hash__(self) -> int:
        return self.value


class Status(enum.Enum):
    """Enumerator for a person's status."""

    # pylint: disable=invalid-name
    unaffected = 1
    affected = 2
    unspecified = 4

    @staticmethod
    def from_name(name: int | str | None) -> Status:
        """Construct and return person status from string."""
        if name is None:
            return Status.unspecified
        if isinstance(name, Status):
            return name
        if isinstance(name, int):
            return Status.from_value(name)
        assert isinstance(name, str)
        name = name.lower()
        if name in {"unaffected", "1", "false"}:
            return Status.unaffected
        if name in {"affected", "2", "true"}:
            return Status.affected
        if name in {"unspecified", "-", "0", "unknown"}:
            return Status.unspecified
        raise ValueError(f"unexpected status type: {name}")

    @staticmethod
    def _internal_value(value: int) -> int:
        return 4 if value == 0 else value

    @staticmethod
    def _external_value(value: int) -> int:
        return 0 if value == 4 else value

    @staticmethod
    def to_value(name: int | str | None) -> int:
        status = Status.from_name(name)
        return Status._external_value(status.value)

    @staticmethod
    def to_name(value: int) -> str:
        return Status(Status._internal_value(value)).name

    @staticmethod
    def from_value(val: int) -> Status:
        return Status(Status._internal_value(int(val)))

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    def short(self) -> str:
        return self.name[0].upper()

    def __ge__(self, other: Status) -> bool:
        if self.__class__ is other.__class__:
            return bool(self.value >= other.value)
        return NotImplemented

    def __gt__(self, other: Status) -> bool:
        if self.__class__ is other.__class__:
            return bool(self.value > other.value)
        return NotImplemented

    def __le__(self, other: Status) -> bool:
        if self.__class__ is other.__class__:
            return bool(self.value <= other.value)
        return NotImplemented

    def __lt__(self, other: Status) -> bool:
        if self.__class__ is other.__class__:
            return bool(self.value < other.value)
        return NotImplemented


class Inheritance(enum.Enum):
    """Enumerator for variant inheritance type."""

    # pylint: disable=invalid-name
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
    def from_name(name: str) -> Inheritance:
        assert (
            name in Inheritance.__members__
        ), f"Inheritance type {name} does not exist!"
        return Inheritance[name]

    @staticmethod
    def from_value(value: int) -> Inheritance:
        return Inheritance(value)

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class Zygosity(enum.Enum):
    """Enumerance for allele zygosity."""

    # pylint: disable=invalid-name
    undefined = 0
    homozygous = 1
    heterozygous = 1 << 1

    @staticmethod
    def from_name(name: str) -> Zygosity:
        assert (
            name in Zygosity.__members__
        ), f"Zygosity type {name} does not exist!"
        return Zygosity[name]

    @staticmethod
    def from_value(value: int) -> Zygosity:
        return Zygosity(value)

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


def bitmask2inheritance(bitmask: int) -> set[Inheritance]:
    """Convert a bitmask to set of inheritance."""
    all_inheritance = {
        Inheritance.reference,
        Inheritance.mendelian,
        Inheritance.denovo,
        Inheritance.omission,
        Inheritance.possible_denovo,
        Inheritance.possible_omission,
        Inheritance.other,
        Inheritance.missing,
        Inheritance.unknown,
    }
    result: set[Inheritance] = set()
    for inh in all_inheritance:
        if bitmask & inh.value:
            result.add(inh)

    return result


class GeneticModel(enum.Enum):
    # pylint: disable=invalid-name
    autosomal = 1
    autosomal_broken = 2
    pseudo_autosomal = 3
    X = 4
    X_broken = 5


class TransmissionType(enum.IntEnum):
    # pylint: disable=invalid-name
    unknown = 0
    transmitted = 1
    denovo = 2
