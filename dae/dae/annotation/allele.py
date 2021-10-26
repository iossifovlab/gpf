from enum import Enum


class Allele:

    class Type(Enum):
        position = 0
        substitution = 1
        small_deletion = 2
        small_insertion = 3
        complex = 4
        large_deletion = 5
        large_duplication = 6

    def __init__(self, chrom: str, pos: int, pos_end: int = None,
                 ref: str = None, alt: str = None,
                 allele_type: Type = None):
        self.chrom = chrom
        self.pos = pos
        self.pos_end = pos_end
        self.ref = ref
        self.alt = alt
        self.allele_type = allele_type

        assert isinstance(self.chrom, str)
        assert isinstance(self.pos, int)
        assert self.pos_end is None or isinstance(self.pos_end, int)
        assert self.alt is None or isinstance(self.alt, str)
        assert self.ref is None or isinstance(self.ref, str)
        assert self.allele_type is None or \
            isinstance(self.allele_type, Allele.Type)

        if not self.allele_type:
            if not self.pos_end and not self.ref and not self.alt:
                self.allele_type = Allele.Type.position
                self.pos_end = self.pos
            elif not self.pos_end and self.ref and self.alt:
                if len(self.ref) == 1 and len(self.alt) == 1:
                    self.allele_type = Allele.Type.substitution
                elif len(self.ref) == 1 and len(self.alt) > 1 and \
                        self.ref[0] == self.alt[0]:
                    self.allele_type == Allele.Type.small_insertion
                elif len(self.ref) > 1 and len(self.alt) == 1 and \
                        self.ref[0] == self.alt[0]:
                    self.allele_type == Allele.Type.small_deletion
                else:
                    self.allele_type == Allele.Type.complex
                self.pos_end = self.pos + len(self.ref) - 1
        if not self.allele_type:
            raise ValueError("Can not determin the type of the variant")

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
