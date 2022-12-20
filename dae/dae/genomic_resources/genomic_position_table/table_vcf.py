from functools import cache
from typing import List
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
        self.header = self._get_header()

    def _open_pysam_file(self):
        return self.genomic_resource.open_vcf_file(self.definition.filename)

    def _get_index_prop_for_special_column(self, key):
        return None

    def _get_header(self):
        if self.header is not None:
            # Don't re-open header if already loaded -
            # This check is useful because we already set the VCF header
            # in the constructor of the class
            return self.header
        assert self.definition.get("header_mode", "file") == "file"
        filename = self.definition.filename
        idx = filename.index(".vcf")
        header_filename = filename[:idx] + ".header" + filename[idx:]
        assert self.genomic_resource.file_exists(header_filename), \
            "VCF tables must have an accompanying *.header.vcf.gz file!"
        return self.genomic_resource.open_vcf_file(header_filename).header.info

    @cache
    def get_file_chromosomes(self) -> List[str]:
        assert isinstance(self.pysam_file, pysam.VariantFile)
        return list(map(str, self.pysam_file.header.contigs))

    def get_line_iterator(self, *args):
        assert isinstance(self.pysam_file, pysam.VariantFile)
        self.stats["tabix fetch"] += 1
        self.buffer.clear()
        for raw_line in self.pysam_file.fetch(*args):
            for allele_index, alt in enumerate(raw_line.alts or [None]):
                assert raw_line.ref is not None
                yield VCFLine(
                    raw_line.contig, raw_line.pos, raw_line.pos,
                    allele_index=allele_index if alt is not None else None,
                    ref=raw_line.ref,
                    alt=alt,
                    info=raw_line.info,
                    info_meta=raw_line.header.info,
                )
