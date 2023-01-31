from __future__ import annotations

import abc
import argparse

from typing import Optional, Dict, Type

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotatable import Position
from dae.annotation.annotatable import Region
from dae.annotation.annotatable import VCFAllele


from dae.tools.cshl2vcf import cshl2vcf
from dae.genomic_resources.genomic_context import GenomicContext


class RecordToAnnotable(abc.ABC):
    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        pass

    @abc.abstractmethod
    def build(self, record: dict[str, str]) -> Annotatable:
        pass


class RecordToPosition(RecordToAnnotable):
    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        super().__init__(columns, context)
        self.chrom_column, self.pos_column = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Position(record[self.chrom_column],
                        int(record[self.pos_column]))


class RecordToRegion(RecordToAnnotable):
    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        super().__init__(columns, context)
        self.chrom_col, self.pos_beg_col, self.pos_end_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Region(record[self.chrom_col],
                      int(record[self.pos_beg_col]),
                      int(record[self.pos_end_col]))


class RecordToVcfAllele(RecordToAnnotable):
    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        super().__init__(columns, context)
        self.chrom_col, self.pos_col, self.ref_col, self.alt_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return VCFAllele(record[self.chrom_col],
                         int(record[self.pos_col]),
                         record[self.ref_col],
                         record[self.alt_col])


class VcfLikeRecordToVcfAllele(RecordToAnnotable):
    """Transform a variant record into VCF allele annotatable."""

    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        super().__init__(columns, context)
        self.vcf_like_col, = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        chrom, pos, ref, alt = record[self.vcf_like_col].split(":")
        return VCFAllele(chrom, int(pos), ref, alt)


class CSHLAlleleRecordToVcfAllele(RecordToAnnotable):
    """Transform a CSHL variant record into a VCF allele annotatable."""

    def __init__(self, columns: tuple, context: Optional[GenomicContext]):
        super().__init__(columns, context)
        if context is None:
            raise ValueError(
                "unable to instantialte CSHLAlleleRecordToVcfAllele "
                "without context")

        self.location_col, self.variant_col = columns
        self.context = context
        self.reference_genome = context.get_reference_genome()
        if self.reference_genome is None:
            raise ValueError(
                "unable to instantialte CSHLAlleleRecordToVcfAllele "
                "without a referrence genome")

    def build(self, record: dict[str, str]) -> Annotatable:
        return VCFAllele(*cshl2vcf(
            record[self.location_col],
            record[self.variant_col],
            self.reference_genome))


RECORD_TO_ANNOTABALE_CONFIGUATION: Dict[tuple, Type[RecordToAnnotable]] = {
    ("chrom", "pos_beg", "pos_end"): RecordToRegion,
    ("chrom", "pos", "ref", "alt"): RecordToVcfAllele,
    ("vcf_like",): VcfLikeRecordToVcfAllele,
    ("chrom", "pos"): RecordToPosition,
    ("location", "variant"): CSHLAlleleRecordToVcfAllele
}


def add_record_to_annotable_arguments(parser: argparse.ArgumentParser):
    all_columns = {
        col for cols in RECORD_TO_ANNOTABALE_CONFIGUATION
        for col in cols}
    for col in all_columns:
        parser.add_argument(f"--col_{col}", default=col,
                            help=f"The column name that stores {col}")


def build_record_to_annotatable(
        parameters: dict[str, str],
        available_columns: set[str],
        context: Optional[GenomicContext] = None) -> RecordToAnnotable:
    """Transform a variant record into an annotable."""
    for columns, record_to_annotabale_class in \
            RECORD_TO_ANNOTABALE_CONFIGUATION.items():
        renamed_columns = [parameters.get(
            f"col_{col}", col) for col in columns]
        all_available = len(
            [cn for cn in renamed_columns if cn not in available_columns]) == 0
        if all_available:
            return record_to_annotabale_class(tuple(renamed_columns), context)
    raise ValueError("no record to annotatable could be found.")
