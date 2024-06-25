from __future__ import annotations

import abc
import argparse
from typing import Optional

from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.cnv_utils import cnv_variant_type, cshl2cnv_variant
from dae.utils.dae_utils import cshl2vcf_variant


class RecordToAnnotable(abc.ABC):
    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        pass

    @abc.abstractmethod
    def build(self, record: dict[str, str]) -> Annotatable:
        pass


class RecordToPosition(RecordToAnnotable):
    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        super().__init__(columns, ref_genome)
        self.chrom_column, self.pos_column = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Position(record[self.chrom_column],
                        int(record[self.pos_column]))


class RecordToRegion(RecordToAnnotable):
    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        super().__init__(columns, ref_genome)
        self.chrom_col, self.pos_beg_col, self.pos_end_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Region(record[self.chrom_col],
                      int(record[self.pos_beg_col]),
                      int(record[self.pos_end_col]))


class RecordToVcfAllele(RecordToAnnotable):
    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        super().__init__(columns, ref_genome)
        self.chrom_col, self.pos_col, self.ref_col, self.alt_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return VCFAllele(record[self.chrom_col],
                         int(record[self.pos_col]),
                         record[self.ref_col],
                         record[self.alt_col])


class VcfLikeRecordToVcfAllele(RecordToAnnotable):
    """Transform a columns record into VCF allele annotatable."""

    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        super().__init__(columns, ref_genome)
        self.vcf_like_col, = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        chrom, pos, ref, alt = record[self.vcf_like_col].split(":")
        return VCFAllele(chrom, int(pos), ref, alt)


class RecordToCNVAllele(RecordToAnnotable):
    """Transform a columns record into a CNV allele annotatable."""

    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        super().__init__(columns, ref_genome)
        self.chrom_col, self.pos_beg_col, self.pos_end_col, self.cnv_type_col \
            = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        cnv_type = cnv_variant_type(record[self.cnv_type_col])
        if cnv_type is None:
            raise ValueError(
                f"unexpected CNV variant type: {record[self.cnv_type_col]}")
        return CNVAllele(
            record[self.chrom_col],
            int(record[self.pos_beg_col]),
            int(record[self.pos_end_col]),
            CNVAllele.Type.from_string(cnv_type))


class CSHLAlleleRecordToAnnotatable(RecordToAnnotable):
    """Transform a CSHL variant record into a VCF allele annotatable."""

    def __init__(self, columns: tuple, ref_genome: Optional[ReferenceGenome]):
        if ref_genome is None:
            raise ValueError(
                "unable to instantiate CSHLAlleleRecordToVcfAllele "
                "without a referrence genome")
        super().__init__(columns, ref_genome)
        self.location_col, self.variant_col = columns
        self.reference_genome = ref_genome

    def build(self, record: dict[str, str]) -> Annotatable:
        variant = record[self.variant_col]
        cnv_type = cnv_variant_type(variant)
        if cnv_type is not None:
            chrom, pos_begin, pos_end, cnv_type = cshl2cnv_variant(
                record[self.location_col],
                record[self.variant_col])
            return CNVAllele(
                chrom, pos_begin, pos_end,
                CNVAllele.Type.from_string(cnv_type))

        return VCFAllele(*cshl2vcf_variant(
            record[self.location_col],
            record[self.variant_col],
            self.reference_genome))


RECORD_TO_ANNOTATABLE_CONFIGURATION: dict[tuple, type[RecordToAnnotable]] = {
    ("chrom", "pos_beg", "pos_end", "cnv_type"): RecordToCNVAllele,
    ("chrom", "pos_beg", "pos_end"): RecordToRegion,
    ("chrom", "pos", "ref", "alt"): RecordToVcfAllele,
    ("vcf_like",): VcfLikeRecordToVcfAllele,
    ("chrom", "pos"): RecordToPosition,
    ("location", "variant"): CSHLAlleleRecordToAnnotatable,
}


def add_record_to_annotable_arguments(parser: argparse.ArgumentParser) -> None:
    all_columns = {
        col for cols in RECORD_TO_ANNOTATABLE_CONFIGURATION
        for col in cols}
    for col in all_columns:
        parser.add_argument(f"--col_{col}", default=col,
                            help=f"The column name that stores {col}")


def build_record_to_annotatable(
        parameters: dict[str, str],
        available_columns: set[str],
        ref_genome: Optional[ReferenceGenome] = None) -> RecordToAnnotable:
    """Transform a variant record into an annotatable."""
    for columns, record_to_annotatable_class in \
            RECORD_TO_ANNOTATABLE_CONFIGURATION.items():
        renamed_columns = [
            parameters.get(f"col_{col}", col) for col in columns
        ]
        all_available = len(
            [cn for cn in renamed_columns if cn not in available_columns],
        ) == 0
        if all_available:
            return record_to_annotatable_class(
                tuple(renamed_columns), ref_genome,
            )
    raise ValueError("no record to annotatable could be found.")
