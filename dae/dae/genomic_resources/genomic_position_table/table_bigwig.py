# pylint: disable=I1101
from collections.abc import Generator
from typing import Optional

from dae.genomic_resources.genomic_position_table.line import Line, LineBase
from dae.genomic_resources.genomic_position_table.table import GenomicPositionTable
from dae.genomic_resources.repository import GenomicResource


class BigWigTable(GenomicPositionTable):
    """bigWig format implementation of the genomic position table."""

    def __init__(
        self,
        genomic_resource: GenomicResource,
        table_definition: dict,
    ):
        super().__init__(genomic_resource, table_definition)
        self.bw_file = None

    def open(self) -> "BigWigTable":
        self.bw_file = self.genomic_resource.open_bigwig_file(
            self.definition.filename)
        if self.bw_file is None:
            raise OSError
        self._set_core_column_keys()
        self._build_chrom_mapping()
        return self

    def close(self) -> None:
        if self.bw_file is not None:
            self.bw_file.close()
        self.bw_file = None

    def get_all_records(self) -> Generator[LineBase, None, None]:
        assert self.bw_file is not None
        for chrom in self.bw_file.chroms().keys():
            for interval in self.bw_file.intervals(chrom):
                yield Line((chrom, *interval))

    def get_records_in_region(
        self,
        chrom: str,
        pos_begin: Optional[int] = None,
        pos_end: Optional[int] = None,
    ) -> Generator[LineBase, None, None]:
        assert self.bw_file is not None

        if chrom not in self.bw_file.chroms():
            raise KeyError
        if pos_begin is None:
            pos_begin = 0
        if pos_end is None:
            pos_end = self.bw_file.chroms()[chrom]

        for interval in self.bw_file.intervals(chrom, pos_begin, pos_end):
            yield Line((chrom, *interval))

    def get_chromosome_length(
        self, chrom: str, _step: int = 100_000_000,
    ) -> int:
        assert self.bw_file is not None
        return self.bw_file.chroms()[chrom]

    def get_file_chromosomes(self) -> list[str]:
        assert self.bw_file is not None
        return list(self.bw_file.chroms().keys())
