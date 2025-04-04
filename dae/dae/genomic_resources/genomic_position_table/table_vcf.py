from __future__ import annotations

from collections.abc import Generator
from functools import cache

import pysam

from dae.genomic_resources.repository import GenomicResource

from .line import VCFLine
from .table_tabix import TabixGenomicPositionTable


class VCFGenomicPositionTable(TabixGenomicPositionTable):
    """Represents a VCF file genome position table."""

    CHROM = "CHROM"
    POS_BEGIN = "POS"
    POS_END = "POS"

    def __init__(
            self, genomic_resource: GenomicResource, table_definition: dict):
        super().__init__(genomic_resource, table_definition)
        self.header = self._load_vcf_header()

    def _load_vcf_header(self) -> pysam.VariantHeaderMetadata:
        assert self.definition.get("header_mode", "file") == "file"
        filename = self.definition.filename
        idx = filename.index(".vcf")
        header_filename = filename[:idx] + ".header" + filename[idx:]
        assert self.genomic_resource.file_exists(header_filename), \
            "VCF tables must have an accompanying *.header.vcf.gz file!"
        return self.genomic_resource.open_vcf_file(header_filename).header.info

    def _transform_vcf_result(self, line: VCFLine) -> None:
        rchrom = self._map_result_chrom(line.chrom)
        assert rchrom is not None
        line.chrom = rchrom

    def _make_vcf_line(
        self, raw_line: pysam.VariantRecord, allele_index: int | None,
    ) -> VCFLine | None:
        line: VCFLine = VCFLine(raw_line, allele_index)
        if not self.rev_chrom_map:
            return line
        if line.fchrom in self.rev_chrom_map:
            self._transform_vcf_result(line)
            return line
        return None

    def open(self) -> VCFGenomicPositionTable:
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

    def get_line_iterator(
        self, chrom: str | None = None, pos_begin: int | None = None,
    ) -> Generator[VCFLine | None, None, None]:
        assert isinstance(self.pysam_file, pysam.VariantFile)

        if chrom is not None:
            fchrom = self.unmap_chromosome(chrom)
            if fchrom is None:
                raise ValueError(
                    f"error in mapping chromosome {chrom} to file contigs: "
                    f"{self.get_file_chromosomes()}")
        else:
            fchrom = None

        self.stats["tabix fetch"] += 1
        self.buffer.clear()
        for raw_line in self.pysam_file.fetch(fchrom, pos_begin):
            allele_index: int | None
            for allele_index, alt in enumerate(raw_line.alts or [None]):
                assert raw_line.ref is not None
                allele_index = allele_index if alt is not None else None
                line = self._make_vcf_line(raw_line, allele_index)
                yield line
