import abc
from collections import deque
from collections.abc import Generator
from typing import Any, Optional, Union

import pysam

Key = Union[str, int]


class LineBase(abc.ABC):
    """Base class for genomic position table lines."""

    def __init__(self) -> None:

        self.chrom: str
        self.fchrom: str
        self.pos_begin: int
        self.pos_end: int
        self.ref: Optional[str]
        self.alt: Optional[str]

    @abc.abstractmethod
    def get(self, key: Key) -> Any:
        """Return score value."""

    @abc.abstractmethod
    def row(self) -> tuple:
        """Return row as tuple."""


class Line(LineBase):
    """Represents a line read from a genomic position table.

    Provides attribute access to a number of important columns - chromosome,
    start position, end position, reference allele and alternative allele.
    """

    def __init__(
        self,
        raw_line: tuple,
        chrom_key: Key = 0,
        pos_begin_key: Key = 1,
        pos_end_key: Key = 2,
        ref_key: Optional[Key] = None,
        alt_key: Optional[Key] = None,
        header: Optional[tuple[str, ...]] = None,
    ):
        super().__init__()

        self._data: tuple[str, ...] = raw_line
        self._header: Optional[tuple[str, ...]] = header

        self.chrom: str = self.get(chrom_key)
        self.fchrom: str = self.get(chrom_key)
        self.pos_begin: int = int(self.get(pos_begin_key))
        self.pos_end: int = int(self.get(pos_end_key))
        self.ref: Optional[str] = \
            self.get(ref_key) if ref_key is not None else None
        self.alt: Optional[str] = \
            self.get(alt_key) if alt_key is not None else None

    def get(self, key: Key) -> str:
        if isinstance(key, int):
            return self._data[key]

        assert self._header is not None
        idx = self._header.index(key)
        return self._data[idx]

    def row(self) -> tuple:
        return self._data


class VCFLine(LineBase):
    """Line adapter for lines derived from a VCF file.

    Implements functionality for handling multi-allelic variants
    and INFO fields.
    """

    def __init__(
            self, raw_line: pysam.VariantRecord, allele_index: Optional[int]):
        super().__init__()

        self.chrom: str = raw_line.contig
        self.fchrom: str = raw_line.contig
        self.pos_begin: int = raw_line.pos
        self.pos_end: int = raw_line.pos

        assert raw_line.ref is not None
        self.ref: str = raw_line.ref
        self.alt: Optional[str] = None
        # Used to handle multiallelic variants in VCF files.
        # The allele index is None if the variant for this line
        # is missing its ALT, i.e. its value is '.'
        self.allele_index: Optional[int] = allele_index
        if self.allele_index is not None:
            assert raw_line.alts is not None
            self.alt = raw_line.alts[self.allele_index]
        self.info: pysam.VariantRecordInfo = raw_line.info
        self.info_meta: pysam.VariantHeaderMetadata = raw_line.header.info

    def get(self, key: Key) -> Any:
        """Get a value from the INFO field of the VCF line."""
        assert isinstance(key, str)

        value, meta = self.info.get(key), self.info_meta.get(key)
        if isinstance(value, tuple):
            if meta.number == "A" and self.allele_index is not None:
                value = value[self.allele_index]
            elif meta.number == "R":
                value = value[
                    self.allele_index + 1
                    if self.allele_index is not None
                    else 0  # Get reference allele value if ALT is '.'
                ]
        return value

    def row(self) -> tuple:
        return ()


class LineBuffer:
    """Represent a line buffer for Tabix genome position table."""

    def __init__(self) -> None:
        self.deque: deque[LineBase] = deque()

    def __len__(self) -> int:
        return len(self.deque)

    def clear(self) -> None:
        self.deque.clear()

    def append(self, line: LineBase) -> None:
        if len(self.deque) > 0 and self.peek_first().chrom != line.chrom:
            self.clear()
        self.deque.append(line)

    def peek_first(self) -> LineBase:
        return self.deque[0]

    def pop_first(self) -> LineBase:
        return self.deque.popleft()

    def peek_last(self) -> LineBase:
        return self.deque[-1]

    def region(self) -> tuple[Optional[str], Optional[int], Optional[int]]:
        """Return region stored in the buffer."""
        if len(self.deque) == 0:
            return None, None, None

        first = self.peek_first()
        last = self.peek_last()

        if first.chrom != last.chrom or first.pos_end > last.pos_end:
            self.clear()
            return None, None, None

        return first.chrom, first.pos_begin, last.pos_end

    def prune(self, chrom: str, pos: int) -> None:
        """Prune the buffer if needed."""
        if len(self.deque) == 0:
            return

        first = self.peek_first()

        if chrom != first.chrom:
            self.clear()
            return

        while len(self.deque) > 0:
            first = self.peek_first()
            if pos <= first.pos_end:
                break
            self.deque.popleft()

    def contains(self, chrom: str, pos: int) -> bool:
        bchrom, bbeg, bend = self.region()
        if bchrom is None or bbeg is None or bend is None:
            return False
        return chrom == bchrom and bend >= pos >= bbeg

    def find_index(self, chrom: str, pos: int) -> int:
        """Find index in line buffer that contains the passed position."""
        if len(self.deque) == 0 or not self.contains(chrom, pos):
            return -1

        if len(self.deque) == 1:
            return 0

        first_index = 0
        last_index = len(self.deque) - 1
        while True:
            mid_index = (last_index - first_index) // 2 + first_index
            if last_index <= first_index:
                break

            mid = self.deque[mid_index]
            if mid.pos_end >= pos >= mid.pos_begin:
                break

            if pos < mid.pos_begin:
                last_index = mid_index - 1
            else:
                first_index = mid_index + 1

        while mid_index > 0:
            prev = self.deque[mid_index - 1]
            if pos > prev.pos_begin:
                break
            mid_index -= 1

        for index in range(mid_index, len(self.deque)):
            line = self.deque[index]
            if line.pos_end >= pos >= line.pos_begin:
                mid_index = index
                break
            if line.pos_begin >= pos:
                mid_index = index
                break

        return mid_index

    def fetch(
        self, chrom: str, pos_begin: int, pos_end: int,
    ) -> Generator[LineBase, None, None]:
        """Return a generator of rows matching the region."""
        beg_index = self.find_index(chrom, pos_begin)
        if beg_index == -1:
            return

        for index in range(beg_index, len(self.deque)):
            row = self.deque[index]
            if row.pos_end < pos_begin:
                continue
            if pos_end is not None and row.pos_begin > pos_end:
                break
            yield row
