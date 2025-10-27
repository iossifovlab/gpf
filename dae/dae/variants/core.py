from __future__ import annotations

import logging
from enum import Enum
from typing import ClassVar

from dae.annotation.annotatable import Annotatable, CNVAllele, VCFAllele
from dae.utils.variant_utils import trim_parsimonious

logger = logging.getLogger(__name__)


class Allele:
    """Class representing alleles."""

    TYPE_DISPLAY_NAME: ClassVar[dict[str, str]] = {
        "substitution": "sub",
        "small_insertion": "ins",
        "small_deletion": "del",
        "complex": "comp",
        "large_duplication": "cnv+",
        "large_deletion": "cnv-",
    }

    DISPLAY_NAME_TYPE: ClassVar[dict[str, str]] = {
        "sub": "substitution",
        "ins": "small_insertion",
        "del": "small_deletion",
        "comp": "complex",
        "complex": "complex",
        "cnv+": "large_duplication",
        "cnv-": "large_deletion",
        "cnv": "cnv",
    }

    class Type(Enum):
        """Enumerator for allele type."""

        # pylint: disable=invalid-name,unsupported-binary-operation
        position = 0
        substitution = 1
        small_insertion = 1 << 1
        small_deletion = 1 << 2
        complex = 1 << 3

        indel = small_insertion | small_deletion | complex

        large_deletion = 1 << 4
        large_duplication = 1 << 5
        cnv = large_deletion | large_duplication

        tandem_repeat = 1 << 6
        tandem_repeat_ins = tandem_repeat | small_insertion
        tandem_repeat_del = tandem_repeat | small_deletion

        def __and__(self, other: Allele.Type) -> int:
            if other is None:
                return 0

            assert isinstance(other, Allele.Type), type(other)
            return self.value & other.value

        def __or__(self, other: Allele.Type) -> int:
            if other is None:
                return 0

            assert isinstance(other, Allele.Type)
            return self.value | other.value

        def __ior__(self, other: Allele.Type) -> Allele.Type:
            if other is None:
                return 0

            assert isinstance(other, Allele.Type)
            return Allele.Type(self.value | other.value)

        def __repr__(self) -> str:
            return Allele.TYPE_DISPLAY_NAME.get(self.name) or self.name

        @classmethod
        def is_cnv(cls, vt: Allele.Type) -> bool:
            if vt is None:
                return False
            if not isinstance(vt, Allele.Type):
                return False
            return bool(vt & cls.cnv)

        @classmethod
        def is_tr(cls, vt: Allele.Type) -> bool:
            if vt is None:
                return False
            if not isinstance(vt, Allele.Type):
                return False
            return bool(vt & cls.tandem_repeat)

    def __init__(
            self, chrom: str, pos: int, *,
            pos_end: int | None = None,
            ref: str | None = None, alt: str | None = None,
            allele_type: Allele.Type | None = None):
        self._chrom: str = chrom
        self._pos: int = pos
        self._pos_end: int | None = pos_end
        self._ref: str | None = ref
        self._alt: str | None = alt
        self._allele_type: Allele.Type

        assert isinstance(self._chrom, str)
        assert isinstance(self._pos, int)
        assert self._pos_end is None or isinstance(self._pos_end, int)
        assert self._alt is None or isinstance(self._alt, str)
        assert self._ref is None or isinstance(self._ref, str)

        if allele_type is not None:
            self._allele_type = allele_type
        else:
            if (not self._pos_end and not self._ref and not self._alt) or \
                    (self._ref and not self._alt):
                self._allele_type = Allele.Type.position
                self._pos_end = self._pos
            elif self._ref and self._alt:
                pos, ref, alt = trim_parsimonious(pos, self._ref, self._alt)

                if len(ref) == 1 and len(alt) == 1:

                    self._allele_type = Allele.Type.substitution

                elif len(ref) == 1 and len(alt) > 1 and ref[0] == alt[0]:
                    self._allele_type = Allele.Type.small_insertion

                elif len(ref) > 1 and len(alt) == 1 and ref[0] == alt[0]:
                    self._allele_type = Allele.Type.small_deletion

                else:
                    self._allele_type = Allele.Type.complex
                if not self._pos_end:
                    self._pos_end = self._pos + len(self._ref) - 1

        if self._allele_type is None or \
                not isinstance(self._allele_type, Allele.Type):
            raise ValueError(
                f"Can not determine the type of variant: "
                f"{self._chrom}:{self._pos} {self._ref}->{self._alt}")

    def get_annotatable(self) -> Annotatable:
        """Return an annotatable version of the allele."""
        if Allele.Type.large_duplication & self.allele_type:
            assert self.end_position is not None
            return CNVAllele(
                self.chrom, self.position, self.end_position,
                Annotatable.Type.LARGE_DUPLICATION)
        if Allele.Type.large_deletion & self.allele_type:
            assert self.end_position is not None
            return CNVAllele(
                self.chrom, self.position, self.end_position,
                Annotatable.Type.LARGE_DELETION)
        if Allele.Type.substitution == self.allele_type:
            assert self.reference is not None
            assert self.alternative is not None
            pos, ref, alt = trim_parsimonious(
                self.position, self.reference, self.alternative)
            return VCFAllele(self.chrom, pos, ref, alt)
        if Allele.Type.indel & self.allele_type:
            assert self.reference is not None
            assert self.alternative is not None
            pos, ref, alt = trim_parsimonious(
                self.position, self.reference, self.alternative)
            return VCFAllele(self.chrom, pos, ref, alt)

        logger.error("unexpected allele: %s", self)
        raise ValueError(f"unexpeced allele: {self}")

    @property
    def chromosome(self) -> str:
        return self._chrom

    @property
    def chrom(self) -> str:
        return self._chrom

    @chrom.setter
    def chrom(self, chrom: str) -> None:
        self._chrom = chrom

    @property
    def position(self) -> int:
        return self._pos

    @property
    def end_position(self) -> int | None:
        return self._pos_end

    @property
    def reference(self) -> str | None:
        return self._ref

    @property
    def alternative(self) -> str | None:
        return self._alt

    @property
    def allele_type(self) -> Allele.Type:
        return self._allele_type

    @staticmethod
    def build_position_allele(chrom: str, pos: int) -> Allele:
        return Allele(chrom, pos)

    @staticmethod
    def build_vcf_allele(
        chrom: str, pos: int, ref: str, alt: str,
    ) -> Allele:
        if ref is not None and alt is not None:
            pos, ref, alt = trim_parsimonious(pos, ref, alt)
        return Allele(chrom, pos, ref=ref, alt=alt)

    @staticmethod
    def build_cnv_allele(
        chrom: str, pos: int, pos_end: int,
        allele_type: Type,
    ) -> Allele:
        return Allele(chrom, pos, pos_end=pos_end, allele_type=allele_type)
