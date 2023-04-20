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
        return \
            f"{self.chrom}:{self.pos}-{self.pos_end} " \
            f"{self.type}"


class Position(Annotatable):

    def __init__(self, chrom, pos):
        super().__init__(
            chrom, pos, pos, Annotatable.Type.POSITION)


class Region(Annotatable):

    def __init__(self, chrom, pos_begin, pos_end):
        super().__init__(
            chrom, pos_begin, pos_end, Annotatable.Type.REGION)


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

        super().__init__(
            chrom, pos, pos_end, allele_type)

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

    def __repr__(self):
        return \
            f"{self.chrom}:{self.pos}-{self.pos_end} " \
            f"vcf({self.ref}->{self.alt}) " \
            f"{self.type}"


class CNVAllele(Annotatable):
    """Defines copy number variants annotatable."""

    def __init__(self, chrom, pos_begin, pos_end, cnv_type):
        assert cnv_type in {
            Annotatable.Type.LARGE_DELETION,
            Annotatable.Type.LARGE_DUPLICATION}, cnv_type

        super().__init__(chrom, pos_begin, pos_end, cnv_type)

    @property
    def ref(self):
        return None

    @property
    def reference(self):
        return None

    @property
    def alt(self):
        return None

    @property
    def alternative(self):
        return None
