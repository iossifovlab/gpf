from __future__ import annotations

import abc
import logging
from collections.abc import Generator
from types import TracebackType
from typing import cast

from box import Box

from dae.genomic_resources.repository import GenomicResource

from .line import Key, Line, LineBase

logger = logging.getLogger(__name__)


class GenomicPositionTable(abc.ABC):
    """Abstraction over genomic scores table."""

    CHROM = "chrom"
    POS_BEGIN = "pos_begin"
    POS_END = "pos_end"
    REF = "reference"
    ALT = "alternative"

    def __init__(
            self, genomic_resource: GenomicResource, table_definition: dict):
        self.genomic_resource = genomic_resource

        self.definition = Box(table_definition)
        self.chrom_map: dict[str, str] | None = None
        self.chrom_order: list[str] | None = None
        self.rev_chrom_map: dict[str, str] | None = None

        self.chrom_key: int
        self.pos_begin_key: int
        self.pos_end_key: int
        self.ref_key: int | None = None
        self.alt_key: int | None = None

        self.header: tuple | None = None

        self.header_mode = self.definition.get("header_mode", "file")
        if self.header_mode == "list":
            self.header = tuple(self.definition.header)
            for hindex, hcolumn in enumerate(self.header):
                if not isinstance(hcolumn, str):
                    raise TypeError(
                        f"The {hindex}-th header {hcolumn} in the table "
                        f"definition is not a string.")
        elif self.header_mode in {"file", "none"}:
            self.header = None
        else:
            raise ValueError(
                f"The 'header_mode' property in a table definition "
                f"must be 'file' [by default], 'none', or 'list'."
                f" The current value {self.header_mode}"
                f"does not meet these requirements.")

    def _build_chrom_mapping(self) -> None:
        self.chrom_map = None
        self.chrom_order = self.get_file_chromosomes()
        if "chrom_mapping" in self.definition:
            mapping = self.definition.chrom_mapping
            if "filename" in mapping:
                self.chrom_map = {}
                self.chrom_order = []
                with self.genomic_resource.open_raw_file(
                        mapping["filename"], "rt") as infile:
                    hcs = infile.readline().strip("\n\r").split("\t")
                    if hcs != ["chrom", "file_chrom"]:
                        raise ValueError(
                            f"The chromosome mapping file "
                            f"{mapping['filename']} in resource "
                            f"{self.genomic_resource.get_id()} is "
                            f"expected to have the two columns "
                            f"'chrom' and 'file_chrom'")
                    for line in infile:
                        chrom, fchrom = line.strip("\n\r").split("\t")
                        assert chrom not in self.chrom_map
                        self.chrom_map[chrom] = fchrom
                        self.chrom_order.append(chrom)
                    assert len(set(self.chrom_map.values())) == \
                        len(self.chrom_map)
            else:
                chromosomes = self.chrom_order
                new_chromosomes: list[str] = chromosomes

                if "del_prefix" in mapping:
                    pref = mapping.del_prefix
                    new_chromosomes = [
                        ch[len(pref):] if ch.startswith(pref) else ch
                        for ch in new_chromosomes
                    ]

                if "add_prefix" in mapping:
                    pref = mapping.add_prefix
                    new_chromosomes = [
                        f"{pref}{chrom}" for chrom in new_chromosomes]
                self.chrom_map = dict(
                    zip(new_chromosomes, chromosomes, strict=True))
                self.chrom_order = new_chromosomes
            self.rev_chrom_map = {
                fch: ch for ch, fch in self.chrom_map.items()}

    def get_column_key(self, col: str) -> int | None:
        """Find the index of a column in the table."""
        if col in self.definition:
            if "index" in self.definition[col]:
                self.definition[col]["column_index"] = \
                    self.definition[col]["index"]
                logger.debug(
                    "%s: Using 'index' to configure columns is outdated,"
                    " use 'column_index' instead.",
                    self.genomic_resource.get_full_id(),
                )
            if "name" in self.definition[col]:
                self.definition[col]["column_name"] = \
                    self.definition[col]["name"]
                logger.debug(
                    "%s: Using 'name' to configure columns is outdated,"
                    " use 'column_name' instead.",
                    self.genomic_resource.get_full_id(),
                )

            if "column_index" in self.definition[col]:
                return cast(int, self.definition[col]["column_index"])
            if "column_name" in self.definition[col]:
                assert self.header is not None
                col_index = self.header.index(
                    self.definition[col]["column_name"])
                self.definition[col]["column_index"] = col_index
                return col_index
        if self.header is not None and col in self.header:
            return self.header.index(col)
        return None

    def _set_core_column_keys(self) -> None:
        # chrom is the first column by default (index 0)
        self.chrom_key = self.get_column_key(self.CHROM) or 0

        # pos_begin is the second column by default (index 1)
        self.pos_begin_key = self.get_column_key(self.POS_BEGIN) or 1

        key = self.get_column_key(self.POS_END)
        if key is not None:
            self.pos_end_key = key
        else:
            if self.header and self.POS_END in self.header:
                self.pos_end_key = 2
            else:
                self.pos_end_key = self.pos_begin_key

        self.ref_key = self.get_column_key(self.REF)
        self.alt_key = self.get_column_key(self.ALT)

    def __enter__(self) -> GenomicPositionTable:
        self.open()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> None:
        self.close()

    @abc.abstractmethod
    def open(self) -> GenomicPositionTable:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Close the resource."""

    @abc.abstractmethod
    def get_all_records(self) -> Generator[LineBase, None, None]:
        """Return generator of all records in the table."""

    @abc.abstractmethod
    def get_records_in_region(
        self, chrom: str,
        pos_begin: int | None = None,
        pos_end: int | None = None,
    ) -> Generator[LineBase, None, None]:
        """Return an iterable over the records in the specified range.

        The interval is closed on both sides and 1-based.
        """

    def get_chromosomes(self) -> list[str]:
        """Return list of contigs in the genomic position table."""
        if self.chrom_order is None:
            raise ValueError(
                f"genomic table not open: "
                f"{self.genomic_resource.resource_id}: "
                f"{self.definition}")
        assert self.chrom_order is not None
        return self.chrom_order

    def _map_file_chrom(self, chrom: str) -> str:
        """Transfrom chromosome name to the chromosomes from score file."""
        if self.chrom_map:
            return self.chrom_map[chrom]
        return chrom

    def _map_result_chrom(self, chrom: str) -> str | None:
        """Transfroms chromosome from score file to the genome chromosomes."""
        assert self.rev_chrom_map is not None
        return self.rev_chrom_map.get(chrom)

    def map_chromosome(self, chromosome: str) -> str | None:
        """Map a chromosome from reference genome to file chromosome."""
        if self.rev_chrom_map is not None:
            if chromosome in self.rev_chrom_map:
                return self.rev_chrom_map[chromosome]
            return None

        return chromosome

    def unmap_chromosome(self, chromosome: str) -> str | None:
        """Map a chromosome file contigs to reference genome chromosome."""
        if self.chrom_map is not None:
            if chromosome in self.chrom_map:
                return self.chrom_map[chromosome]
            return None

        return chromosome

    @abc.abstractmethod
    def get_chromosome_length(
            self, chrom: str, step: int = 100_000_000) -> int:
        """Return the length of a chromosome (or contig).

        Returned value is guarnteed to be larget than the actual contig length.
        """

    @abc.abstractmethod
    def get_file_chromosomes(self) -> list[str]:
        """Return chromosomes in a genomic table file.

        This is to be overwritten by the subclass. It should return a list of
        the chromosomes in the file in the order determinted by the file.
        """


def get_idx(key: Key, header: tuple) -> int:
    if isinstance(key, int):
        return key
    assert header is not None
    return header.index(key)


def zero_based_adjust(
    raw: tuple,
    pos_begin_key: Key,
    pos_end_key: Key,
    header: tuple,
) -> tuple:
    """Adjust a zero-based record."""
    rec = list(raw)
    pos_begin_key = get_idx(pos_begin_key, header)
    pos_end_key = get_idx(pos_end_key, header)

    rec[pos_begin_key] = int(rec[pos_begin_key]) + 1
    rec[pos_end_key] = int(rec[pos_end_key])
    if rec[pos_end_key] < rec[pos_begin_key]:
        rec[pos_end_key] += 1
    return tuple(map(str, rec))


def adjust_zero_based_line(line: Line) -> Line:
    """Adjust a zero-based line."""
    if line.pos_begin == line.pos_end:
        line.pos_end += 1
    line.pos_begin += 1

    return line
