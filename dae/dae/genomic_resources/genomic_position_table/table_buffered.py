from collections.abc import Generator

from dae.genomic_resources.genomic_position_table.line import Line, LineBase
from dae.genomic_resources.genomic_position_table.table import (
    GenomicPositionTable,
)
from dae.genomic_resources.genomic_position_table.table_bigwig import BigWigTable
from dae.utils.regions import Region


import cProfile
pr = cProfile.Profile()

class BufferedTable(GenomicPositionTable):
    """Wrapper class to provide buffering for GenomicPositionTable."""

    def __init__(self, table: BigWigTable, fetch_size: int = 2000):
        super().__init__(table.genomic_resource, table.definition)
        self._table = table
        self._buffer: list[tuple[int, int, float]] = []
        self._buffer_region: Region = Region("?", -1, -1)
        self.fetch_size = fetch_size

    def open(self) -> GenomicPositionTable:
        self._table.open()
        self._set_core_column_keys()
        self._build_chrom_mapping()
        return self

    def close(self) -> None:
        self._table.close()

    def get_chromosome_length(self, chrom: str, step: int = 100_000_000) -> int:
        return self._table.get_chromosome_length(chrom, step)

    def get_file_chromosomes(self) -> list[str]:
        return self._table.get_file_chromosomes()

    def _fill(self, chrom: str, start: int, stop: int) -> None:
        """
        Attempts to fill the buffer with records for the given range.

        Will fetch in ranges of length ``fetch_size`` starting from ``start``
        until either results are found or ``stop`` is reached.
        """
        self._buffer = tuple()
        self._buffer_region = Region("?", -1, -1)

        range_start = max(0, start - 1)
        chromlen = self._table.chroms[chrom]
        range_stop = min(chromlen, range_start + self.fetch_size)
        stop = min(stop, chromlen)
        
        res = self._table.bw_file.intervals(chrom, range_start, range_stop)
        while not res and range_stop < stop:
            range_start = range_stop
            range_stop = range_start + self.fetch_size
            range_stop = min(chromlen, range_stop)
            print(range_start, range_stop)
            res = self._table.bw_file.intervals(chrom, range_start, range_stop)

        self._buffer = res or []
        if res:
            self._buffer_region = Region(
                chrom,
                self._buffer[0][0] + 1,
                self._buffer[-1][1])

    @staticmethod
    def _binary_search(q_start: int, q_stop: int, start: int, stop: int) -> int:
        if q_stop < start:
            return -1
        if q_start > stop:
            return 1
        return 0

    def _find(self, chrom: str, pos_begin: int, pos_end: int) -> int:
        query = Region(chrom, pos_begin, pos_end)
        if not query.intersects(self._buffer_region):
            return -1
        idx: int = len(self._buffer) // 2
        # do binary search on buffer, get idx
        l_bound = 0
        r_bound = len(self._buffer) - 1
        while l_bound <= r_bound:
            idx = (r_bound + l_bound) // 2
            line = self._buffer[idx]
            res = BufferedTable._binary_search(
                pos_begin, pos_end, line[0], line[1])
            if res == 1:
                l_bound = idx + 1
            elif res == -1 or res == 0:
                r_bound = idx - 1
        return idx

    def get_all_records(self) -> Generator[LineBase, None, None]:
        yield from self._table.get_all_records()

    def get_records_in_region(
        self, chrom: str,
        pos_begin: int | None = None,
        pos_end: int | None = None,
    ) -> Generator[LineBase, None, None]:
        fchrom = self._map_file_chrom(chrom)
        if fchrom not in self.get_file_chromosomes():
            raise KeyError
        if pos_begin is None:
            pos_begin = 0
        if pos_end is None:
            pos_end = self.get_chromosome_length(chrom)

        pos_current = pos_begin

        idx = self._find(fchrom, pos_begin, pos_end)
        if idx == -1:
            self._fill(fchrom, pos_begin, pos_end)
            idx = self._find(fchrom, pos_begin, pos_end)

        while pos_current <= pos_end and self._buffer:
            line = self._buffer[idx]
            yield Line((chrom, *line))
            pos_current = line[1] + 1
            idx += 1
            if idx == len(self._buffer):
                self._fill(fchrom, pos_current, pos_end)
                idx = 0
