from __future__ import annotations

import abc
from typing import Optional, Dict, List, Union, cast, Generator
from types import TracebackType

from box import Box

from dae.genomic_resources.repository import GenomicResource
from .line import LineBase


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
        self.chrom_map: Optional[Dict[str, str]] = None
        self.chrom_order: Optional[List[str]] = None
        self.rev_chrom_map: Optional[Dict[str, str]] = None

        self.chrom_key: Optional[Union[int, str]] = None
        self.pos_begin_key: Optional[Union[int, str]] = None
        self.pos_end_key: Optional[Union[int, str]] = None
        self.ref_key: Optional[Union[int, str]] = None
        self.alt_key: Optional[Union[int, str]] = None

        self.header: Optional[tuple] = None

        self.header_mode = self.definition.get("header_mode", "file")
        if self.header_mode == "list":
            self.header = tuple(self.definition.header)
            for hindex, hcolumn in enumerate(self.header):
                if not isinstance(hcolumn, str):
                    raise ValueError(
                        f"The {hindex}-th header {hcolumn} in the table "
                        f"definition is not a string.")
        elif self.header_mode in {"file", "none"}:
            self.header = None
        else:
            raise ValueError(
                f"The 'header' property in a table definition "
                f"must be 'file' [by default], 'none', or a "
                f"list of strings. The current value "
                f"{self.header_mode} does not meet these "
                f"requirements.")

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
                self.chrom_map = dict(zip(new_chromosomes, chromosomes))
                self.chrom_order = new_chromosomes
            self.rev_chrom_map = {
                fch: ch for ch, fch in self.chrom_map.items()}

    def _get_column_key(self, col: str) -> Optional[Union[int, str]]:
        if col not in self.definition:
            return None
        if "name" in self.definition[col]:
            return cast(str, self.definition[col].name)
        if "index" in self.definition[col]:
            return cast(int, self.definition[col].index)
        return None

    def _set_core_column_keys(self) -> None:
        self.chrom_key = self._get_column_key(self.CHROM)
        if self.chrom_key is None:
            self.chrom_key = self.CHROM

        self.pos_begin_key = self._get_column_key(self.POS_BEGIN)
        if self.pos_begin_key is None:
            self.pos_begin_key = self.POS_BEGIN

        self.pos_end_key = self._get_column_key(self.POS_END)
        if self.pos_end_key is None:
            if self.header and self.POS_END in self.header:
                self.pos_end_key = self.POS_END
            else:
                self.pos_end_key = self.pos_begin_key

        self.ref_key = self._get_column_key(self.REF)
        self.alt_key = self._get_column_key(self.ALT)

    def __enter__(self) -> GenomicPositionTable:
        self.open()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: Optional[BaseException],
            exc_tb: TracebackType | None) -> None:
        self.close()

    @abc.abstractmethod
    def open(self) -> GenomicPositionTable:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Close the resource."""

    @abc.abstractmethod
    def get_all_records(self) -> Generator[Optional[LineBase], None, None]:
        """Return generator of all records in the table."""

    @abc.abstractmethod
    def get_records_in_region(
        self, chrom: str,
        pos_begin: Optional[int] = None,
        pos_end: Optional[int] = None
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

    def map_chromosome(self, chromosome: str) -> Optional[str]:
        """Map a chromosome from reference genome to file chromosome."""
        if self.rev_chrom_map is not None:
            if chromosome in self.rev_chrom_map:
                return self.rev_chrom_map[chromosome]
            return None

        return chromosome

    def unmap_chromosome(self, chromosome: str) -> Optional[str]:
        """Map a chromosome file contigs to reference genome chromosome."""
        if self.chrom_map is not None:
            if chromosome in self.chrom_map:
                assert chromosome in self.chrom_map
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
    def get_file_chromosomes(self) -> List[str]:
        """Return chromosomes in a genomic table file.

        This is to be overwritten by the subclass. It should return a list of
        the chromomes in the file in the order determinted by the file.
        """
