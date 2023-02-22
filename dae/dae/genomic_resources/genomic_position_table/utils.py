import os
# pylint: disable=no-member
import pysam  # type: ignore

from dae.genomic_resources.repository import GenomicResource
from .table import GenomicPositionTable
from .table_inmemory import InmemoryGenomicPositionTable
from .table_tabix import TabixGenomicPositionTable
from .table_vcf import VCFGenomicPositionTable


def build_genomic_position_table(
    resource: GenomicResource, table_definition: dict
) -> GenomicPositionTable:
    """Instantiate a genome position table from a genomic resource."""
    filename = table_definition["filename"]

    if filename.endswith(".bgz"):
        default_format = "tabix"
    elif filename.endswith(".vcf.gz"):
        default_format = "vcf_info"
    elif filename.endswith(".txt") or filename.endswith(".txt.gz") or \
            filename.endswith(".tsv") or filename.endswith(".tsv.gz"):
        default_format = "tsv"
    elif filename.endswith(".csv") or filename.endswith(".csv.gz"):
        default_format = "csv"
    else:
        default_format = "mem"

    table_fmt = table_definition.get("format", default_format)

    if table_fmt in ("mem", "csv", "tsv"):
        return InmemoryGenomicPositionTable(resource, table_definition,
                                            table_fmt)
    if table_fmt == "tabix":
        return TabixGenomicPositionTable(resource, table_definition)
    if table_fmt == "vcf_info":
        return VCFGenomicPositionTable(resource, table_definition)

    raise ValueError(f"unknown table format {table_fmt}")


def save_as_tabix_table(
        table: GenomicPositionTable,
        full_file_path: str):
    """Save a genome position table as Tabix table."""
    tmp_file = full_file_path + ".tmp"
    with open(tmp_file, "wt", encoding="utf8") as text_file:
        if table.header_mode != "none":
            print("#" + "\t".join(table.header), file=text_file)
        for rec in table.get_all_records():
            print(*rec, sep="\t", file=text_file)
    pysam.tabix_compress(tmp_file, full_file_path, force=True)
    os.remove(tmp_file)

    pysam.tabix_index(full_file_path, force=True,
                      seq_col=table.chrom_key,
                      start_col=table.pos_begin_key,
                      end_col=table.pos_end_key)
