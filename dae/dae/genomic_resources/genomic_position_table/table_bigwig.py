from __future__ import annotations

from collections.abc import Generator

from dae.genomic_resources.genomic_position_table.line import BigWigLine
from dae.genomic_resources.genomic_position_table.table import (
    GenomicPositionTable,
)
from dae.genomic_resources.repository import GenomicResource
from dae.utils.regions import Region


class BigWigTable(GenomicPositionTable):
    """bigWig format implementation of the genomic position table."""

    def __init__(
        self,
        genomic_resource: GenomicResource,
        table_definition: dict,
    ):
        super().__init__(genomic_resource, table_definition)
        self._bw_file = None
        self.chroms: dict[str, int] = {}
        self._buffer: list[tuple[int, int, float]] = []
        self._buffer_region: Region = Region("?", -1, -1)

        self.direct_fetch_size = self.definition.get("direct_fetch_size", 50)
        self.buffer_fetch_size = self.definition.get("buffer_fetch_size", 500)
        self.use_buffered_threshold = \
            self.definition.get("use_buffered_threshold", 500)

        # this forces the initial fetch to be made directly
        self._last_pos = -(self.use_buffered_threshold + 1)

    def open(self) -> BigWigTable:
        self._bw_file = self.genomic_resource.open_bigwig_file(
            self.definition.filename)
        if self._bw_file is None:
            raise OSError
        self.chroms = self._bw_file.chroms()
        self._set_core_column_keys()
        self._build_chrom_mapping()
        return self

    def close(self) -> None:
        if self._bw_file is not None:
            self._bw_file.close()
        self._bw_file = None

    def _fill(self, chrom: str, start: int, stop: int) -> None:
        """
        Attempts to fill the buffer with records for the given range.

        Will fetch in ranges of length ``buffer_fetch_size`` starting from
        ``start`` until either results are found or ``stop`` is reached.
        """
        assert self._bw_file is not None
        self._buffer = []
        self._buffer_region = Region("?", -1, -1)

        chromlen = self.chroms[chrom]
        range_start = start
        range_stop = min(chromlen, range_start + self.buffer_fetch_size)
        stop = min(stop, chromlen)

        res = self._bw_file.intervals(chrom, range_start, range_stop)
        while not res and range_stop < stop:
            range_start = range_stop
            range_stop = range_start + self.buffer_fetch_size
            range_stop = min(chromlen, range_stop)
            res = self._bw_file.intervals(chrom, range_start, range_stop)

        self._buffer = res or []
        if res:
            self._buffer_region = Region(
                chrom,
                self._buffer[0][0] + 1,
                self._buffer[-1][1])

    def _find(self, chrom: str, pos_begin: int, pos_end: int) -> int:

        def _left_right_helper(
            q_start: int, q_stop: int,
            start: int, stop: int,
        ) -> int:
            if q_stop <= start:
                return -1
            if q_start >= stop:
                return 1
            return 0

        query = Region(chrom, pos_begin + 1, pos_end)
        if not query.intersects(self._buffer_region):
            return -1

        # do binary search on buffer, get idx
        idx: int = len(self._buffer) // 2
        l_bound = 0
        r_bound = len(self._buffer) - 1
        while l_bound <= r_bound:
            idx = (r_bound + l_bound) // 2
            line = self._buffer[idx]
            res = _left_right_helper(
                pos_begin, pos_end, line[0], line[1])
            if res == 1:
                l_bound = idx + 1
            elif res == -1:
                r_bound = idx - 1
            elif res == 0:
                if idx == 0:
                    return idx
                prevline = self._buffer[idx - 1]
                subres = _left_right_helper(
                    pos_begin, pos_end, prevline[0], prevline[1])
                if subres == 0:
                    r_bound = idx - 1
                else:
                    return idx
        return idx

    def _fetch_buffered(
        self, chrom: str, pos_begin: int, pos_end: int,
    ) -> Generator[tuple[int, int, float], None, None]:
        pos_current = pos_begin

        idx = self._find(chrom, pos_begin, pos_begin + 1)
        if idx == -1:
            self._fill(chrom, pos_begin, pos_end)
            idx = self._find(chrom, pos_begin, pos_begin + 1)

        if idx == -1:
            # there's no direct match for (pos_begin, pos_begin + 1), but
            # we set the idx to 0 anyways since there might be something
            # in the buffer to yield (since _fill is called with pos_end)
            idx = 0

        while self._buffer:
            line = self._buffer[idx]
            if line[0] + 1 > pos_end:
                return
            yield (line[0] + 1, line[1], line[2])
            pos_current = line[1]
            if pos_current >= pos_end:
                return
            idx += 1
            if idx == len(self._buffer):
                self._fill(chrom, pos_current, pos_end)
                idx = 0

    def _fetch_direct(
        self, chrom: str, pos_begin: int, pos_end: int,
    ) -> Generator[tuple[int, int, float], None, None]:
        assert self._bw_file is not None
        chrom_len = self.chroms[chrom]
        pos_end = min(pos_end, chrom_len)

        start = pos_begin
        stop = min(start + self.direct_fetch_size, pos_end)
        while start < pos_end:
            intervals = self._bw_file.intervals(chrom, start, stop)
            while intervals is None:
                start = stop
                stop = min(start + self.direct_fetch_size, pos_end)
                if start >= pos_end:
                    return
                intervals = self._bw_file.intervals(chrom, start, stop)
            start = intervals[-1][1]
            stop = min(start + self.direct_fetch_size, pos_end)

            for interval in intervals:
                yield (interval[0] + 1, interval[1], interval[2])

    def get_records_in_region(
        self,
        chrom: str | None = None,
        pos_begin: int | None = None,
        pos_end: int | None = None,
    ) -> Generator[BigWigLine, None, None]:

        if chrom is None:
            yield from self.get_all_records()
            return

        fchrom = self._map_file_chrom(chrom)
        if fchrom not in self.chroms:
            raise KeyError
        if pos_begin is None:
            pos_begin = 0
        if pos_end is None:
            pos_end = self.chroms[fchrom]

        pos_begin = max(0, pos_begin - 1)

        fetch_method = self._fetch_buffered \
            if pos_begin - self._last_pos <= self.use_buffered_threshold \
            else self._fetch_direct

        self._last_pos = pos_begin

        for interval in fetch_method(fchrom, pos_begin, pos_end):
            yield BigWigLine((chrom, *interval))

    def get_all_records(self) -> Generator[BigWigLine, None, None]:
        assert self._bw_file is not None
        for chrom in self.get_chromosomes():
            yield from self.get_records_in_region(chrom)

    def get_chromosome_length(
        self, chrom: str,
        step: int = 100_000_000,  # noqa: ARG002
    ) -> int:
        assert self._bw_file is not None
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
        return self.chroms[fchrom]

    def get_file_chromosomes(self) -> list[str]:
        assert self._bw_file is not None
        return list(self.chroms.keys())
