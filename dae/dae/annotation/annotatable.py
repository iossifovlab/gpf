from __future__ import annotations
import enum


class Annotatable:
    """Base class for annotatables used in annotation pipeline."""

    class Type(enum.Enum):
        """Defines annotatable types."""

        POSITION = 0
        REGION = 1

        SUBSTITUTION = 2
        SMALL_INSERTION = 3
        SMALL_DELETION = 4
        COMPLEX = 5

        LARGE_DUPLICATION = 6
        LARGE_DELETION = 7

        @staticmethod
        def from_string(variant: str) -> Annotatable.Type:
            """Construct annotatable type from string argument."""
            # pylint: disable=too-many-return-statements
            vtype = variant.lower()
            if vtype == "position":
                return Annotatable.Type.POSITION
            if vtype == "region":
                return Annotatable.Type.REGION
            if vtype == "substitution":
                return Annotatable.Type.SUBSTITUTION
            if vtype == "small_insertion":
                return Annotatable.Type.SMALL_INSERTION
            if vtype == "small_deletion":
                return Annotatable.Type.SMALL_DELETION
            if vtype == "complex":
                return Annotatable.Type.COMPLEX
            if vtype == "large_duplication":
                return Annotatable.Type.LARGE_DUPLICATION
            if vtype == "large_deletion":
                return Annotatable.Type.LARGE_DELETION
            raise ValueError(f"unexpected annotatable type: {variant}")

    def __init__(self, chrom, pos, pos_end, annotatable_type):
        self._chrom = chrom
        self._pos = pos
        self._pos_end = pos_end
        self.type = annotatable_type

    @property
    def chrom(self):
        return self._chrom

    @property
    def chromosome(self):
        return self._chrom

    @property
    def pos(self):
        return self._pos

    @property
    def position(self):
        return self._pos

    @property
    def end_position(self):
        return self._pos_end

    @property
    def pos_end(self):
        return self._pos_end

    def __len__(self):
        return self._pos_end - self._pos + 1

    def __repr__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        if not isinstance(other, Annotatable):
            return False
        return self.type == other.type and self.chrom == other.chrom and \
            self.pos == other.pos and self.pos_end == other.pos_end

    @staticmethod
    def tokenize(value: str) -> tuple[str, list[str]]:
        # value := TYPE(arg1, arg2, ...)
        tokens = value.split("(")
        if len(tokens) != 2:
            raise ValueError("Attempted to tokenize invalid input - ", value)
        return tokens[0], tokens[1].rstrip(")").replace(" ", "").split(",")

    @staticmethod
    def from_string(value: str) -> Annotatable:
        a_type, _ = Annotatable.tokenize(value)
        if a_type in ("Position", "POSITION"):
            return Position.from_string(value)
        if a_type in ("Region", "REGION"):
            return Region.from_string(value)
        if a_type in ("VCFAllele", "SUBSTITUTION", "COMPLEX",
                      "SMALL_DELETION", "SMALL_INSERTION"):
            return VCFAllele.from_string(value)
        if a_type in ("CNVAllele", "LARGE_DUPLICATION", "LARGE_DELETION"):
            return CNVAllele.from_string(value)
        raise ValueError("No matching Annotatable type found for: ", value)


class Position(Annotatable):

    def __init__(self, chrom, pos):
        super().__init__(
            chrom, pos, pos, Annotatable.Type.POSITION)

    def __repr__(self) -> str:
        return f"Position({self.chrom},{self.pos})"

    @staticmethod
    def from_string(value: str) -> Position:
        a_type, args = Annotatable.tokenize(value)
        if a_type not in ("Position", "POSITION"):
            raise ValueError()
        if len(args) != 2:
            raise ValueError()
        return Position(args[0], int(args[1]))


class Region(Annotatable):

    def __init__(self, chrom, pos_begin, pos_end):
        super().__init__(
            chrom, pos_begin, pos_end, Annotatable.Type.REGION)

    def __repr__(self) -> str:
        return f"Region({self.chrom},{self.pos},{self.pos_end})"

    @staticmethod
    def from_string(value: str) -> Region:
        a_type, args = Annotatable.tokenize(value)
        if a_type not in ("Region", "REGION"):
            raise ValueError()
        if len(args) != 3:
            raise ValueError()
        return Region(args[0], int(args[1]), int(args[2]))


class VCFAllele(Annotatable):
    """Defines small variants annotatable."""

    def __init__(self, chrom, pos, ref, alt):
        assert ref is not None
        assert alt is not None

        self._ref = ref
        self._alt = alt

        allele_type = None
        if len(ref) == 1 and len(alt) == 1:
            allele_type = Annotatable.Type.SUBSTITUTION
            pos_end = pos
        elif len(ref) == 1 and len(alt) > 1 and ref[0] == alt[0]:
            allele_type = Annotatable.Type.SMALL_INSERTION
            pos_end = pos + 1
        elif len(ref) > 1 and len(alt) == 1 and ref[0] == alt[0]:
            allele_type = Annotatable.Type.SMALL_DELETION
            pos_end = pos + len(ref)
        else:
            allele_type = Annotatable.Type.COMPLEX
            pos_end = pos + len(ref)

        super().__init__(chrom, pos, pos_end, allele_type)

    @property
    def ref(self):
        return self._ref

    @property
    def reference(self):
        return self._ref

    @property
    def alt(self):
        return self._alt

    @property
    def alternative(self):
        return self._alt

    def __repr__(self) -> str:
        return f"VCFAllele({self.chrom},{self.pos},{self.pos_end}" \
               f",{self.ref},{self.alt})"

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if not isinstance(other, VCFAllele):
            return False
        return self.ref == other.ref and self.alt == other.alt

    @staticmethod
    def from_string(value: str) -> VCFAllele:
        a_type, args = Annotatable.tokenize(value)
        if a_type not in ("VCFAllele", "SUBSTITUTION", "COMPLEX",
                          "SMALL_DELETION", "SMALL_INSERTION"):
            raise ValueError()
        if len(args) != 4:
            raise ValueError()
        return VCFAllele(args[0], int(args[1]), args[2], args[3])


class CNVAllele(Annotatable):
    """Defines copy number variants annotatable."""

    def __init__(self, chrom, pos_begin, pos_end, cnv_type):
        assert cnv_type in {
            Annotatable.Type.LARGE_DELETION,
            Annotatable.Type.LARGE_DUPLICATION}, cnv_type

        super().__init__(chrom, pos_begin, pos_end, cnv_type)

    def __repr__(self) -> str:
        return f"CNVAllele({self.chrom},{self.pos},{self.pos_end},{self.type})"

    @staticmethod
    def from_string(value: str) -> CNVAllele:
        a_type, args = Annotatable.tokenize(value)
        if a_type == "CNVAllele":
            if len(args) != 4:
                raise ValueError()
            cnv_type = Annotatable.Type.from_string(args[3])
        elif a_type in ("LARGE_DUPLICATION", "LARGE_DELETION"):
            if len(args) != 3:
                raise ValueError()
            cnv_type = Annotatable.Type.from_string(a_type)
        else:
            raise ValueError()
        return CNVAllele(args[0], int(args[1]), int(args[2]), cnv_type)
