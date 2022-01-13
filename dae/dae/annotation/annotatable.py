import enum


class Annotatable:

    class Type(enum.Enum):
        position = 0
        region = 1

        substitution = 2
        small_insertion = 3
        small_deletion = 4
        complex = 5

        large_duplication = 6
        large_deletion = 7

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
        super(Position, self).__init__(
            chrom, pos, pos, Annotatable.Type.position)


class Region(Position):

    def __init__(self, chrom, pos_begin, pos_end):
        super(Position, self).__init__(
            chrom, pos_begin, pos_end, Annotatable.Type.region)


class VCFAllele(Annotatable):

    def __init__(self, chrom, pos, ref, alt):
        assert ref is not None
        assert alt is not None

        self._ref = ref
        self._alt = alt

        allele_type = None
        if len(ref) == 1 and len(alt) == 1:
            allele_type = Annotatable.Type.substitution
            pos_end = pos

        elif len(ref) == 1 and len(alt) > 1 and ref[0] == alt[0]:
            allele_type = Annotatable.Type.small_insertion
            pos_end = pos + 1

        elif len(ref) > 1 and len(alt) == 1 and ref[0] == alt[0]:

            allele_type = Annotatable.Type.small_deletion
            pos_end = pos + len(ref)
        else:
            allele_type = Annotatable.Type.complex
            pos_end = pos + len(ref)

        super(VCFAllele, self).__init__(
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

    def __init__(self, chrom, pos_begin, pos_end, cnv_type):
        assert cnv_type in {
            Annotatable.Type.large_deletion,
            Annotatable.Type.large_duplication}, cnv_type

        super(CNVAllele, self).__init__(chrom, pos_begin, pos_end, cnv_type)

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
