from functools import cache
from copy import copy
from typing import Optional

# pylint: disable=no-member
import pysam  # type: ignore

from .line import VCFLine
from .table_tabix import TabixGenomicPositionTable


class VCFGenomicPositionTable(TabixGenomicPositionTable):
    """Represents a VCF file genome position table."""

    CHROM = "CHROM"
    POS_BEGIN = "POS"
    POS_END = "POS"

    def __init__(self, genomic_resource, table_definition):
        super().__init__(genomic_resource, table_definition)
        self.header = self._load_header()

    def _load_header(self):
        assert self.definition.get("header_mode", "file") == "file"
        filename = self.definition.filename
        idx = filename.index(".vcf")
        header_filename = filename[:idx] + ".header" + filename[idx:]
        assert self.genomic_resource.file_exists(header_filename), \
            "VCF tables must have an accompanying *.header.vcf.gz file!"
        return self.genomic_resource.open_vcf_file(header_filename).header.info

    def _transform_result(self, line):
        rchrom = self._map_result_chrom(line.chrom)
        if rchrom is None:
            return None
        new_line = copy(line)
        new_line.chrom = rchrom
        return new_line

    def open(self):
        self.pysam_file = self.genomic_resource.open_vcf_file(
            self.definition.filename)
        self._set_core_column_keys()
        self._build_chrom_mapping()
        return self

    @cache  # pylint: disable=method-cache-max-size-none
    def get_file_chromosomes(self) -> list[str]:
        with self.genomic_resource.open_tabix_file(
                self.definition.filename) as pysam_file_tabix:
            contigs = pysam_file_tabix.contigs
        return list(map(str, contigs))

    def get_line_iterator(self, *args):
        assert isinstance(self.pysam_file, pysam.VariantFile)
        self.stats["tabix fetch"] += 1
        self.buffer.clear()
        for raw_line in self.pysam_file.fetch(*args):
            allele_index: Optional[int]
            for allele_index, alt in enumerate(raw_line.alts or [None]):
                assert raw_line.ref is not None
                allele_index = allele_index if alt is not None else None
                yield VCFLine(raw_line, allele_index)
