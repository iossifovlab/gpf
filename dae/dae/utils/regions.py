from __future__ import annotations

import copy
import logging
from collections import defaultdict
from collections.abc import Iterator, Sequence
from typing import Any, Optional, Union

import pysam

logger = logging.getLogger(__name__)


MAX_POSITION = 3_000_000_000


def coalesce(v1: Optional[int], v2: int) -> int:
    """Return first non-None value."""
    if v1 is not None:
        return v1
    return v2


def split_into_regions(
        chrom: str, chrom_length: int,
        region_size: int) -> list[Region]:
    """Return a list of regions for a chrom with a given length."""
    regions = []

    current_start = 1
    while current_start < chrom_length + 1:
        end = min(chrom_length, current_start + region_size - 1)
        regions.append(Region(chrom, current_start, end))
        current_start = current_start + region_size

    return regions


def get_chromosome_length_tabix(
    tabix_file: Union[pysam.TabixFile, pysam.VariantFile], chrom: str,
    step: int = 100_000_000, precision: int = 5_000_000,
) -> Optional[int]:
    """
    Return the length of a chromosome (or contig).

    Returned value is guarnteed to be larger than the actual contig length.
    """
    def any_records(riter: Iterator) -> bool:
        try:
            next(riter)
        except StopIteration:
            return False
        except ValueError:
            return False

        return True
    try:
        # First we find any region that includes the last record i.e.
        # the length of the chromosome
        left, right = None, None
        pos = step
        while left is None or right is None:
            region = Region(chrom, pos, None)
            if any_records(tabix_file.fetch(str(region))):
                left = pos
                pos = pos * 2
            else:
                right = pos
                pos = pos // 2
        # Second we use binary search to narrow the region until we find the
        # index of the last element (in left) and the length (in right)
        while (right - left) > precision:
            pos = (left + right) // 2
            region = Region(chrom, pos, None)
            if any_records(tabix_file.fetch(str(region))):
                left = pos
            else:
                right = pos
    except ValueError as ex:
        logger.warning(
            "unable to find length of contig %s: %s", chrom, ex)
        return None
    else:
        return right


class Region:
    """Class representing a genomic region."""

    def __init__(
        self, chrom: str,
        start: Optional[int] = None, stop: Optional[int] = None,
    ):
        if start is not None and not isinstance(start, int):
            raise TypeError(f"Invalid type for start position - {type(start)}")
        if stop is not None and not isinstance(stop, int):
            raise TypeError(f"Invalid type for stop position - {type(stop)}")
        if start is not None and stop is not None:
            assert start <= stop

        self.chrom = chrom
        self._start = start
        self._stop = stop

    @property
    def start(self) -> Optional[int]:
        return self._start

    @property
    def stop(self) -> Optional[int]:
        return self._stop

    @property
    def begin(self) -> Optional[int]:
        return self.start

    @property
    def end(self) -> Optional[int]:
        return self.stop

    def __repr__(self) -> str:
        if self.start is None:
            return self.chrom
        if self.end is None:
            return f"{self.chrom}:{self.start}"
        return f"{self.chrom}:{self.start}-{self.stop}"

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Region):
            return False
        return bool(
            self.chrom == other.chrom
            and self.start == other.start
            and self.stop == other.stop,
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def isin(self, chrom: str, pos: int) -> bool:
        """Check if a genomic position is insde of the region."""
        if chrom != self.chrom:
            return False

        if self.start and pos < self.start:
            return False
        return not self.stop or pos <= self.stop

    @staticmethod
    def _min(a: Optional[int], b: Optional[int]) -> Optional[int]:
        if a is None:
            return b
        if b is None:
            return a
        return min(a, b)

    @staticmethod
    def _max(a: Optional[int], b: Optional[int]) -> Optional[int]:
        if a is None:
            return b
        if b is None:
            return a
        return max(a, b)

    @staticmethod
    def _make_region(
        chrom: str, start: Optional[int], stop: Optional[int],
    ) -> Optional[Region]:
        if chrom is None:
            return None
        if start is not None and stop is not None and start > stop:
            return None
        return Region(chrom, start, stop)

    def intersection(self, other: Region) -> Optional[Region]:
        """Return intersection of the region with other region."""
        if self.chrom != other.chrom:
            return None
        if self.start is None and self.stop is None:
            return Region(other.chrom, other.start, other.stop)
        if other.start is None and other.stop is None:
            return Region(self.chrom, self.start, self.stop)
        if self.start is None:
            assert self.stop is not None
            return self._make_region(
                self.chrom, other.start, self._min(self.stop, other.stop))
        if self.stop is None:
            assert self.start is not None
            return self._make_region(
                self.chrom, self._max(self.start, other.start), other.stop)

        assert self.start is not None
        assert self.stop is not None
        return self._make_region(
            self.chrom,
            self._max(self.start, other.start),
            self._min(self.stop, other.stop),
        )

    def contains(self, other: Region) -> bool:
        """Check if the region contains other region."""
        if self.chrom != other.chrom:
            return False
        if self.start is None and self.stop is None:
            return True
        if self.start is None:
            assert self.stop is not None
            if other.stop is not None:
                assert other.stop is not None
                return bool(other.stop <= self.stop)
            return False
        if self.stop is None:
            assert self.start is not None
            if other.start is not None:
                return other.start >= self.start
            return False

        assert self.start is not None
        assert self.stop is not None
        if other.stop is None or other.start is None:
            return False
        return self.start <= other.start \
            and other.stop <= self.stop

    def intersects(self, other: Region) -> bool:
        """Check if the region intersects another."""
        if self.chrom != other.chrom:
            return False
        if self.start is not None and self.stop is not None:
            if other.start is None or other.stop is None:
                return other.intersects(self)
            return not (self.stop < other.start or self.start > other.stop)
        if self.stop is not None:
            return other.start is None or self.stop >= other.start

        if self.start is not None:
            return other.stop is None or self.start <= other.stop

        return True

    @staticmethod
    def from_str(region: str) -> Region:
        """Parse string representation of a region."""
        parts = [p.strip() for p in region.split(":")]
        if len(parts) == 1:
            return Region(parts[0], None, None)
        if len(parts) == 2:
            chrom = parts[0]
            parts = [p.strip() for p in parts[1].split("-")]
            start = int(parts[0].replace(",", ""))
            if len(parts) == 1:
                return BedRegion(chrom, start, start)
            if len(parts) == 2:
                stop = int(parts[1].replace(",", ""))
                return BedRegion(chrom, start, stop)

        raise ValueError(f"unexpeced format for region {region}")


class BedRegion(Region):
    """Represents proper bed regions."""

    def __init__(
        self, chrom: str,
        start: int, stop: int,
    ):
        assert start is not None
        assert stop is not None
        assert stop >= start

        super().__init__(chrom, start, stop)

    @property
    def start(self) -> int:
        assert self._start is not None
        return self._start

    @property
    def stop(self) -> int:
        assert self._stop is not None
        return self._stop

    @property
    def begin(self) -> int:
        return self.start

    @property
    def end(self) -> int:
        return self.stop

    def __len__(self) -> int:
        return self.stop - self.start


def collapse(
    source: Sequence[Region], *,
    is_sorted: bool = False,
) -> list[Region]:
    """Collapse list of regions."""
    if not source:
        return list(source)

    regions = copy.deepcopy(list(source))

    if not is_sorted:
        regions.sort(key=lambda x: x.start if x.start is not None else -1)

    collapsed: dict[str, list[Region]] = defaultdict(list)

    collapsed[regions[0].chrom].append(regions[0])

    for reg in regions[1:]:
        chrom_collapsed = collapsed.get(reg.chrom)
        if not chrom_collapsed:
            collapsed[reg.chrom].append(reg)
            continue
        prev_reg = chrom_collapsed[-1]

        if coalesce(reg.start, 1) <= coalesce(prev_reg.stop, 1):
            if coalesce(reg.stop, 1) > coalesce(prev_reg.stop, 1):
                last = collapsed[reg.chrom][-1]
                collapsed[reg.chrom][-1] = \
                    Region(last.chrom, last.start, reg.stop)
            continue

        collapsed[reg.chrom].append(reg)

    result = []
    for v in list(collapsed.values()):
        result.extend(v)
    return result
