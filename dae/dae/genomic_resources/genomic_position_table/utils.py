import os

import pysam

from dae.genomic_resources.repository import GenomicResource

from .table import GenomicPositionTable
from .table_bigwig import BigWigTable
from .table_inmemory import InmemoryGenomicPositionTable
from .table_tabix import TabixGenomicPositionTable
from .table_vcf import VCFGenomicPositionTable


def build_genomic_position_table(
    resource: GenomicResource, table_definition: dict,
) -> GenomicPositionTable:
    """Instantiate a genome position table from a genomic resource."""
    filename = table_definition["filename"]

    if filename.endswith(".bgz"):
        default_format = "tabix"
    elif filename.endswith(".vcf.gz"):
        default_format = "vcf_info"
    elif filename.endswith((".txt", ".txt.gz", ".tsv", ".tsv.gz")):
        default_format = "tsv"
    elif filename.endswith((".csv", ".csv.gz")):
        default_format = "csv"
    elif filename.endswith(".bw"):
        default_format = "bw"
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
    if table_fmt.lower() in ("bw", "bigwig"):
        return BigWigTable(resource, table_definition)

    raise ValueError(f"unknown table format {table_fmt}")


def save_as_tabix_table(
        table: GenomicPositionTable,
        full_file_path: str) -> None:
    """Save a genome position table as Tabix table."""
    tmp_file = full_file_path + ".tmp"
    with open(tmp_file, "wt", encoding="utf8") as text_file:
        if table.header_mode != "none":
            assert table.header is not None
            print("#" + "\t".join(table.header), file=text_file)
        for rec in table.get_all_records():
            print(*rec.row(), sep="\t", file=text_file)
    pysam.tabix_compress(tmp_file, full_file_path, force=True)
    os.remove(tmp_file)

    chrom_key: int | None
    pos_begin_key: int | None
    pos_end_key: int | None

    if isinstance(table.chrom_key, str):
        assert table.header is not None
        chrom_key = table.header.index(table.chrom_key)
    else:
        chrom_key = table.chrom_key

    if isinstance(table.pos_begin_key, str):
        assert table.header is not None
        pos_begin_key = table.header.index(table.pos_begin_key)
    else:
        pos_begin_key = table.pos_begin_key

    if isinstance(table.pos_end_key, str):
        assert table.header is not None
        pos_end_key = table.header.index(table.pos_end_key)
    else:
        pos_end_key = table.pos_end_key

    pysam.tabix_index(full_file_path, force=True,
                      seq_col=chrom_key,
                      start_col=pos_begin_key,
                      end_col=pos_end_key)
