from __future__ import annotations

import logging
import pathlib
from collections.abc import Sequence
from types import TracebackType

import pysam

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


class VcfSerializer:
    """Stores a sequence of alleles in a VCF file."""

    def __init__(
            self,
            families: FamiliesData,
            genome: ReferenceGenome,
            output_path: pathlib.Path,
    ):
        self.families = families
        self.genome = genome
        self.output_path = output_path
        self._vcf_header = self._build_vcf_header()
        self.vcf_file: pysam.VariantFile | None = None

    def serialize(
        self,
        full_variants: Sequence[tuple[SummaryVariant, list[FamilyVariant]]],
    ) -> None:
        """Serialize a sequence of alleles to a VCF file."""
        assert self.vcf_file is not None
        for sv, fvs in full_variants:
            record = self._build_vcf_record(sv, fvs)
            self.vcf_file.write(record)

    def _build_vcf_header(self) -> pysam.VariantHeader:
        header = pysam.VariantHeader()
        for contig in self.genome.chromosomes:
            header.contigs.add(contig)
        for fam in self.families.values():
            for p in fam.members_in_order:
                header.add_sample(p.sample_id)
        header.formats.add("GT", 1, "String", "Genotype")

        return header

    def _build_vcf_file(self) -> pysam.VariantFile:
        header = self._build_vcf_header()
        return pysam.VariantFile(
            str(self.output_path), "w", header=header,
        )

    def _build_vcf_record(
            self,
            sv: SummaryVariant,
            fvs: list[FamilyVariant],
    ) -> pysam.VariantRecord:
        assert self.vcf_file is not None
        record = self.vcf_file.new_record()
        record.contig = sv.chrom
        record.pos = sv.position
        record.ref = sv.reference
        record.alts = sv.alternative

        for fv in fvs:
            fam = self.families[fv.family_id]
            for mem_index, mem in enumerate(fam.members_in_order):
                record.samples[mem.sample_id]["GT"] = fv.genotype[mem_index]
        return record

    def __enter__(self) -> VcfSerializer:
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            logger.error(
                "exception while working with genomic score: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        self.close()

    def close(self) -> None:
        if self.vcf_file is not None:
            self.vcf_file.close()
            self.vcf_file = None

    def open(self) -> VcfSerializer:
        self.vcf_file = self._build_vcf_file()
        return self
