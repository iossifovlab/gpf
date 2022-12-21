from __future__ import annotations

import abc
from typing import Optional, Dict, List, Union, Tuple
from functools import cached_property
from box import Box  # type: ignore

from dae.genomic_resources.repository import GenomicResource


class GenomicPositionTable(abc.ABC):
    """Abstraction over genomic scores table."""

    CHROM = "chrom"
    POS_BEGIN = "pos_begin"
    POS_END = "pos_end"

    def __init__(self, genomic_resource: GenomicResource, table_definition):
        self.genomic_resource = genomic_resource

        self.definition = Box(table_definition)
        self.chrom_map: Optional[Dict[str, str]] = None
        self.chrom_order: Optional[List[str]] = None
        self.rev_chrom_map: Optional[Dict[str, str]] = None

        self.chrom_column_i = None
        self.pos_begin_column_i = None
        self.pos_end_column_i = None

        # handling the header property
        self.header: Optional[tuple] = None

        self.header_mode = self.definition.get("header_mode", "file")
        if self.header_mode == "list":
            self.header = tuple(self.definition.header)
            for hindex, hcolumn in enumerate(self.header):
                if not isinstance(hcolumn, str):
                    raise ValueError(
                        f"The {hindex}-th header {hcolumn} in the table "
                        f"definition is not a string.")
        else:
            if self.header_mode in {"file", "none"}:
                self.header = None
            else:
                raise ValueError(
                    f"The 'header' property in a table definition "
                    f"must be 'file' [by default], 'none', or a "
                    f"list of strings. The current value "
                    f"{self.header_mode} does not meet these "
                    f"requirements.")

    def _build_chrom_mapping(self):
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
                new_chromosomes = chromosomes

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

    def _set_special_column_indexes(self):
        self.chrom_column_i = self.get_special_column_index(self.CHROM)
        self.pos_begin_column_i = self.get_special_column_index(self.POS_BEGIN)
        self.pos_end_column_i = self.pos_begin_column_i
        try:
            self.pos_end_column_i = self.get_special_column_index(self.POS_END)
        except (ValueError, KeyError):
            definition = self.definition.to_dict()
            definition[self.POS_END] = {"index": self.pos_end_column_i}
            self.definition = Box(definition)

    def get_column_names(self):
        return self.header

    def _get_index_prop_for_special_column(self, key):
        index_prop = key + ".index"

        if key not in self.definition:
            raise KeyError(f"The table definition has no index "
                           f"({index_prop} property) for the special "
                           f"column {key}.")
        if "index" not in self.definition[key]:
            raise KeyError(f"The table definition has no index "
                           f"({index_prop} property) for the special "
                           f"column {key}.")

        try:
            return int(self.definition[key].index)
        except ValueError as ex:
            raise ValueError(f"The {index_prop} property in the table "
                             f"definition should be an integer.") from ex

    def get_special_column_index(self, key):
        """Get special columns index."""
        if self.header_mode == "none" or not self.header:
            return self._get_index_prop_for_special_column(key)
        try:
            return self._get_index_prop_for_special_column(key)
        except KeyError:
            column_name = self.get_special_column_name(key)
            try:
                return self.header.index(column_name)
            except ValueError as ex:
                raise ValueError(f"The column {column_name} for the "
                                 f"special column {key} is not in the "
                                 f"header.") from ex

    def get_special_column_name(self, key):
        if self.header_mode == "none":
            raise AttributeError("The table has no header.")
        if key in self.definition and "name" in self.definition[key]:
            return self.definition[key].name
        return key

    def _get_other_columns(self) -> Union[Tuple[None, None], zip]:
        if self.header is not None:
            return zip(*(
                (i, x) for i, x in enumerate(self.header)
                if i not in (self.chrom_column_i,
                             self.pos_begin_column_i,
                             self.pos_end_column_i)
            ))
        return None, None

    @cached_property
    def ref_key(self):
        """Get the index or name of the column for the reference base."""
        ref_key = None
        if "reference" in self.definition:
            ref_key = self.get_special_column_index("reference") \
                if self.header_mode == "none" \
                else self.get_special_column_name("reference")
        return ref_key

    @cached_property
    def alt_key(self):
        """Get the index or name of the column for the alternative base."""
        alt_key = None
        if "alternative" in self.definition:
            alt_key = self.get_special_column_index("alternative") \
                if self.header_mode == "none" \
                else self.get_special_column_name("alternative")
        return alt_key

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    @abc.abstractmethod
    def open(self) -> GenomicPositionTable:
        pass

    @abc.abstractmethod
    def close(self):
        """Close the resource."""

    @abc.abstractmethod
    def get_all_records(self):
        pass

    @abc.abstractmethod
    def get_records_in_region(
            self, chrom: str, pos_begin: int = None, pos_end: int = None):
        """Return an iterable over the records in the specified range.

        The interval is closed on both sides and 1-based.
        """

    def get_chromosomes(self):
        return self.chrom_order

    @abc.abstractmethod
    def get_file_chromosomes(self) -> List[str]:
        """Return chromosomes in a genomic table file.

        This is to be overwritten by the subclass. It should return a list of
        the chromomes in the file in the order determinted by the file.
        """

    def get_chromosome_length(self, chrom, step=1_000_000):
        """Return the length of a chromosome (or contig).

        The returned value is
        the index of the last record for the chromosome + 1.
        """
        def any_records(riter):
            try:
                next(riter)
            except StopIteration:
                return False
            else:
                return True

        # First we find any region that includes the last record i.e.
        # the length of the chromosome
        left, right = None, None
        pos = step
        while left is None or right is None:
            if any_records(self.get_records_in_region(chrom, pos, None)):
                left = pos
                pos = pos * 2
            else:
                right = pos
                pos = pos // 2

        # Second we use binary search to narrow the region until we find the
        # index of the last element (in left) and the length (in right)
        while (right - left) > 1:
            pos = (left + right) // 2
            if any_records(self.get_records_in_region(chrom, pos, None)):
                left = pos
            else:
                right = pos
        return right
