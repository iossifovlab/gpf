from __future__ import annotations

from collections.abc import Generator

from dae.genomic_resources.genomic_position_table.line import Line, LineBase
from dae.genomic_resources.genomic_position_table.table import (
    GenomicPositionTable,
)
from dae.genomic_resources.repository import GenomicResource


class BigWigTable(GenomicPositionTable):
    """bigWig format implementation of the genomic position table."""

    BATCH_SIZE = 2000

    def __init__(
        self,
        genomic_resource: GenomicResource,
        table_definition: dict,
    ):
        super().__init__(genomic_resource, table_definition)
        self.bw_file = None

    def open(self) -> BigWigTable:
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

    def _intervals(
        self, chrom: str, pos_begin: int, pos_end: int,
    ) -> Generator[tuple[int, int, float], None, None]:
        assert self.bw_file is not None
        chrom_len = self.bw_file.chroms()[chrom]
        pos_end = min(pos_end, chrom_len)

        start = max(0, pos_begin - 1)
        stop = min(start + self.BATCH_SIZE, pos_end)
        while start < pos_end:
            intervals = self.bw_file.intervals(chrom, start, stop)
            while intervals is None:
                start = stop
                stop = min(start + self.BATCH_SIZE, pos_end)
                if start >= pos_end:
                    return
                intervals = self.bw_file.intervals(chrom, start, stop)
            start = intervals[-1][1]
            stop = min(start + self.BATCH_SIZE, pos_end)
            for interval in intervals:
                yield (interval[0] + 1, interval[1], interval[2])

    def get_records_in_region(
        self,
        chrom: str,
        pos_begin: int | None = None,
        pos_end: int | None = None,
    ) -> Generator[LineBase, None, None]:
        assert self.bw_file is not None
        fchrom = self._map_file_chrom(chrom)

        if fchrom not in self.bw_file.chroms():
            raise KeyError
        if pos_begin is None:
            pos_begin = 0
        if pos_end is None:
            pos_end = self.bw_file.chroms()[fchrom]

        for interval in self._intervals(fchrom, pos_begin, pos_end):
            yield Line((chrom, *interval))

    def get_all_records(self) -> Generator[LineBase, None, None]:
        assert self.bw_file is not None
        for chrom in self.get_chromosomes():
            yield from self.get_records_in_region(chrom)

    def get_chromosome_length(
        self, chrom: str, _step: int = 100_000_000,
    ) -> int:
        assert self.bw_file is not None
        if chrom not in self.get_chromosomes():
            raise ValueError(
                f"contig {chrom} not present in the table's contigs: "
                f"{self.get_chromosomes()}")
        fchrom = self._map_file_chrom(chrom)
        if fchrom is None:
            raise ValueError(
                f"error in mapping chromsome {chrom} to the file contigs: "
                f"{self.get_file_chromosomes()}",
            )
        if fchrom not in self.get_file_chromosomes():
            raise ValueError(
                f"contig {fchrom} not present in the file's contigs: "
                f"{self.get_file_chromosomes()}",
            )
        return self.bw_file.chroms()[fchrom]

    def get_file_chromosomes(self) -> list[str]:
        assert self.bw_file is not None
        return list(self.bw_file.chroms().keys())
