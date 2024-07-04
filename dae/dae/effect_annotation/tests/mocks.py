# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
from typing import cast

from dae.genomic_resources.gene_models import Exon
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.regions import Region


class TranscriptModelMock:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self, strand: str,
        cds_start: int, cds_end: int,
        exons: list[Exon],
        coding: list[Exon] | None = None,
        is_coding: bool = True,
    ):
        self.strand = strand
        self.cds = [cds_start, cds_end]
        self.exons = exons
        self.chrom = "1"
        self.gene = "B"
        self.tr_id = "123"
        self.tr_name = "123"

        if coding is None:
            self.coding = self.exons
        else:
            self.coding = coding
        self._is_coding = is_coding

    def cds_regions(self) -> list[Region]:
        return cast(list[Region], self.coding)

    def is_coding(self) -> bool:
        return self._is_coding

    def all_regions(self) -> list[Region]:
        return cast(list[Region], self.exons)


class ReferenceGenomeMock:

    def get_sequence(
        self, chromosome: str, pos: int, pos_last: int,
    ) -> str:
        print(("get", chromosome, pos, pos_last))
        return "".join([chr(i) for i in range(pos, pos_last + 1)])


class CodeMock:
    # pylint: disable=too-few-public-methods
    startCodons = ["ABC", "DEF"]
    CodonsAaKeys: dict = {}


class AnnotatorMock:
    # pylint: disable=too-few-public-methods

    def __init__(self, reference_genome: ReferenceGenome):
        self.reference_genome = reference_genome
        self.code = CodeMock()
        self.promoter_len = 0
