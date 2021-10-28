from enum import Enum
from typing import Optional


class Allele:

    TYPE_DISPLAY_NAME = {
        "substitution": "sub",
        "small_insertion": "ins",
        "small_deletion": "del",
        "complex": "comp",
        "large_insertion": "cnv+",
        "large_deletion": "cnv-",
    }

    class Type(Enum):
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

        def __and__(self, other):
            assert isinstance(other, Allele.Type), type(other)
            return self.value & other.value

        def __or__(self, other):
            assert isinstance(other, Allele.Type)
            return self.value | other.value

        def __ior__(self, other):
            assert isinstance(other, Allele.Type)
            return Allele.Type(self.value | other.value)

        @staticmethod
        def from_name(name):
            name = name.lower().strip()
            if name == "sub" or name == "substitution":
                return Allele.Type.substitution
            elif name == "ins" or name == "insertion":
                return Allele.Type.small_insertion
            elif name == "del" or name == "deletion":
                return Allele.Type.small_deletion
            elif name == "comp" or name == "complex":
                return Allele.Type.complex
            elif name in {"cnv_p", "cnv+", "large_duplication"}:
                return Allele.Type.large_duplication
            elif name in {"cnv_m", "cnv-", "large_deletion"}:
                return Allele.Type.large_deletion
            elif name in {"tr", "tandem_repeat"}:
                return Allele.Type.tandem_repeat

            raise ValueError(f"unexpected variant type: {name}")

        @staticmethod
        def from_cshl_variant(variant):
            # FIXME: Change logic to use entire string
            if variant is None:
                return Allele.Type.invalid

            vt = variant[0:2]
            if vt == "su":
                return Allele.Type.substitution
            elif vt == "in":
                return Allele.Type.small_insertion
            elif vt == "de":
                return Allele.Type.small_deletion
            elif vt == "co":
                return Allele.Type.complex
            elif vt == "TR":
                return Allele.Type.tandem_repeat
            elif variant == "CNV+":
                return Allele.Type.large_duplication
            elif variant == "CNV-":
                return Allele.Type.large_duplication
            else:
                raise ValueError(f"unexpected variant type: {variant}")

        @staticmethod
        def from_value(value):
            if value is None:
                return None
            return Allele.Type(value)

        @staticmethod
        def is_cnv(vt):
            if vt is None:
                return False
            assert isinstance(vt, Allele.Type)
            return vt & Allele.Type.cnv

        @staticmethod
        def is_tr(vt):
            if vt is None:
                return False
            assert isinstance(vt, Allele.Type)
            return vt & Allele.Type.tandem_repeat

        def __repr__(self) -> str:
            return Allele.TYPE_DISPLAY_NAME.get(self.name) or self.name

        def __str__(self) -> str:
            return Allele.TYPE_DISPLAY_NAME.get(self.name) or self.name

        def __lt__(self, other):
            return self.value < other.value

    def __init__(self, chrom: str, pos: int, pos_end: int = None,
                 ref: str = None, alt: str = None,
                 allele_type: Type = None):
        self._chrom: str = chrom
        self._pos: int = pos
        self._pos_end: int = pos_end
        self._ref: Optional[str] = ref
        self._alt: Optional[str] = alt
        self._allele_type: Allele.Type = allele_type

        assert isinstance(self._chrom, str)
        assert isinstance(self._pos, int)
        assert self._pos_end is None or isinstance(self._pos_end, int)
        assert self._alt is None or isinstance(self._alt, str)
        assert self._ref is None or isinstance(self._ref, str)
        assert self._allele_type is None or \
            isinstance(self._allele_type, Allele.Type)

        if not self._allele_type:

            if not self._pos_end and not self._ref and not self._alt:
                self._allele_type = Allele.Type.position
                self._pos_end = self._pos
            elif self._ref and not self._alt:
                self._allele_type = Allele.Type.position
                self._pos_end = self._pos
            elif self._ref and self._alt:

                if len(self._ref) == 1 and len(self._alt) == 1:

                    self._allele_type = Allele.Type.substitution

                elif len(self._ref) == 1 and len(self._alt) > 1 and \
                        self._ref[0] == self._alt[0]:

                    self._allele_type = Allele.Type.small_insertion

                elif len(self._ref) > 1 and len(self._alt) == 1 and \
                        self._ref[0] == self._alt[0]:

                    self._allele_type = Allele.Type.small_deletion

                else:
                    self._allele_type = Allele.Type.complex
                if not self._pos_end:
                    self._pos_end = self._pos + len(self._ref) - 1

        if not self._allele_type:
            raise ValueError(
                f"Can not determine the type of the variant: "
                f"{self._chrom}:{self._pos} {self._ref}->{self._alt}")

    @property
    def chromosome(self) -> str:
        return self._chrom

    @property
    def chrom(self) -> str:
        return self._chrom

    @property
    def position(self) -> int:
        return self._pos

    @property
    def end_position(self) -> int:
        return self._pos_end

    @property
    def reference(self) -> Optional[str]:
        return self._ref

    @property
    def alternative(self) -> Optional[str]:
        return self._alt

    @property
    def allele_type(self) -> Type:
        return self._allele_type

    @staticmethod
    def build_position_allele(chrom: str, pos: int):
        return Allele(chrom, pos)

    @staticmethod
    def build_vcf_allele(chrom: str, pos: int, ref: str, alt: str):
        return Allele(chrom, pos, ref=ref, alt=alt)

    @staticmethod
    def build_cnv_allele(chrom: str, pos: int, pos_end,
                         allele_type: Type):
        return Allele(chrom, pos, pos_end, allele_type=allele_type)
