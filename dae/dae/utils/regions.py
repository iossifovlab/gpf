from __future__ import annotations

import copy
import logging
from collections import defaultdict
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import networkx as nx
import pysam

logger = logging.getLogger(__name__)


MAX_POSITION = 3_000_000_000


def coalesce(v1: int | None, v2: int) -> int:
    """Return first non-None value."""
    if v1 is not None:
        return v1
    return v2


def bedfile2regions(bed_filename: str) -> list[BedRegion]:
    """Transform BED file into list of regions."""
    with open(bed_filename) as infile:
        regions = []
        for line in infile:
            if line[0] == "#":
                continue
            chrom, sbeg, send = line.strip().split("\t")
            beg = int(sbeg)
            end = int(send)
            regions.append(BedRegion(chrom, beg + 1, end))
        return regions


def regions2bedfile(regions: list[BedRegion], bed_filename: str) -> None:
    """Save list of regions into a BED file."""
    result = "\n".join(
        f"{reg.chrom}\t{reg.start - 1}\t{reg.stop}\n"
        for reg in regions
    )
    Path(bed_filename).write_text(result)


def calc_bin_begin(bin_len: int, bin_idx: int) -> int:
    """
    Calculates the 1-based start position of the <bin_idx>-th bin
    of length <bin_len>.

    n       2n      3n      4n
    |_______|_______|_______|
     bin_len \
              \
               bin_begin
    """
    return (bin_len * bin_idx) + 1


def calc_bin_end(bin_len: int, bin_idx: int) -> int:
    """
    Calculates the 1-based end position of the <bin_idx>-th bin
    of length <bin_len>.

    n       2n      3n      4n
    |_______|_______|_______|
     bin_len        \
                     \
                      bin_end
    """
    return bin_len * (bin_idx + 1)


def calc_bin_index(bin_len: int, pos: int) -> int:
    """
    Calculates the index of the <bin_len>-long bin the given 1-based
    position <pos> falls into.

    n       2n      3n      4n
    |_______|_______|_______|
     (bin 0) (bin 1) (bin 2)
    """
    return (pos - 1) // bin_len


def split_into_regions(
        chrom: str, chrom_length: int,
        region_size: int, start: int = 1) -> list[Region]:
    """Return a list of regions for a chrom with a given length."""

    if region_size == 0:
        return [Region(chrom)]

    region_size = min(region_size, chrom_length)
    return [
        Region(chrom,
               calc_bin_begin(region_size, i),
               calc_bin_end(region_size, i))
        for i in range(calc_bin_index(region_size, start),
                       calc_bin_index(region_size, chrom_length) + 1)
    ]


def get_chromosome_length_tabix(
    tabix_file: pysam.TabixFile | pysam.VariantFile, chrom: str,
    step: int = 100_000_000, precision: int = 5_000_000,
) -> int | None:
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
                if pos == 0:  # stop infinite loop if any_records is never True
                    raise ValueError  # noqa: TRY301
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
        return right  # noqa: TRY300

    except ValueError as ex:
        logger.warning(
            "unable to find length of contig %s: %s", chrom, ex)
        return None


class Region:
    """Class representing a genomic region."""

    def __init__(
        self, chrom: str,
        start: int | None = None, stop: int | None = None,
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
    def start(self) -> int | None:
        return self._start

    @property
    def stop(self) -> int | None:
        return self._stop

    @property
    def begin(self) -> int | None:
        return self.start

    @property
    def end(self) -> int | None:
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
        return not (self.stop and pos > self.stop)

    @staticmethod
    def _min(a: int | None, b: int | None) -> int | None:
        if a is None:
            return b
        if b is None:
            return a
        return min(a, b)

    @staticmethod
    def _max(a: int | None, b: int | None) -> int | None:
        if a is None:
            return b
        if b is None:
            return a
        return max(a, b)

    @staticmethod
    def _make_region(
        chrom: str, start: int | None, stop: int | None,
    ) -> Region | None:
        if chrom is None:
            return None
        if start is not None and stop is not None and start > stop:
            return None
        return Region(chrom, start, stop)

    def intersection(self, other: Region) -> Region | None:
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
        parts = [p.strip() for p in region.rsplit(":", maxsplit=1)]
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

    @staticmethod
    def from_str(region: str) -> BedRegion:
        """Parse string representation of a region."""
        result = Region.from_str(region)
        if result.start is None or result.stop is None:
            raise ValueError(f"Invalid region format: {region}")
        return BedRegion(result.chrom, result.start, result.stop)

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
        return self.stop - self.start + 1


def all_regions_from_chrom(regions: list[Region], chrom: str) -> list[Region]:
    """Subset of regions in R that are from chr."""
    return [r for r in regions if r.chrom == chrom]


def unique_regions(regions: list[Region]) -> list[Region]:
    """Remove duplicated regions."""
    return list(set(regions))


def connected_component(regions: list[BedRegion]) -> Any:
    """Return connected component of regions.

    This might be the same as collapse.
    """
    graph = nx.Graph()

    graph.add_nodes_from(regions)
    regions_by_chrom = defaultdict(list)
    for reg in regions:
        regions_by_chrom[reg.chrom].append(reg)

    for nds in regions_by_chrom.values():
        nds.sort(key=lambda x: x.stop)
        for k in range(1, len(nds)):
            for j in range(k - 1, -1, -1):
                if nds[k].start <= nds[j].stop:
                    graph.add_edge(nds[k], nds[j])
                else:
                    break
    return nx.connected_components(graph)


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


def collapse_no_chrom(
    source: list[BedRegion], *,
    is_sorted: bool = False,
) -> list[BedRegion]:
    """Collapse by ignoring the chromosome.

    Useful when the caller knows
    that all the regions are from the same chromosome.
    """
    if not source:
        return source
    regions = copy.copy(source)
    if len(regions) == 1:
        return regions

    if not is_sorted:
        regions.sort(key=lambda x: x.start)

    collapsed = [regions[0]]
    for reg in regions[1:]:
        prev_reg = collapsed[-1]
        if reg.start <= prev_reg.stop:
            if reg.stop > prev_reg.stop:
                prev_reg = BedRegion(prev_reg.chrom, prev_reg.start, reg.stop)
                collapsed[-1] = prev_reg
            continue

        collapsed.append(reg)

    return collapsed


def total_length(regions: list[BedRegion]) -> int:
    return sum(len(x) for x in regions)


def intersection(
    regions1: list[Region], regions2: list[Region],
) -> list[Region]:
    """Compute intersection of two list of regions.

    First collapses each for lists of regions s1 and s2 and then find
    the intersection.
    """
    s1_c = collapse(regions1)
    s2_c = collapse(regions2)
    s1_c.sort(key=lambda x: (x.chrom, x.start))
    s2_c.sort(key=lambda x: (x.chrom, x.start))

    intersect = []

    k = 0

    for i in s2_c:
        while k < len(s1_c):
            if i.chrom != s1_c[k].chrom:
                if i.chrom > s1_c[k].chrom:
                    k += 1
                    continue
                break
            if coalesce(i.stop, 1) < coalesce(s1_c[k].start, 1):
                break
            if coalesce(i.start, 1) > coalesce(s1_c[k].stop, MAX_POSITION):
                k += 1
                continue
            if coalesce(i.start, 1) <= coalesce(s1_c[k].start, 1):
                if coalesce(i.stop, MAX_POSITION) >= \
                        coalesce(s1_c[k].stop, MAX_POSITION):
                    intersect.append(s1_c[k])
                    k += 1
                    continue
                new_i = Region(i.chrom, s1_c[k].start, i.stop)
                intersect.append(new_i)
                break
            if coalesce(i.start, 1) > coalesce(s1_c[k].start, 1):
                if coalesce(i.stop, MAX_POSITION) <= \
                        coalesce(s1_c[k].stop, MAX_POSITION):
                    intersect.append(i)
                    break
                new_i = Region(i.chrom, i.start, s1_c[k].stop)
                intersect.append(new_i)
                k += 1
                continue

    return intersect


def union(*r: list[Region]) -> list[Region]:
    """Collapse many lists of regions."""
    r_sum = [el for rlist in r for el in rlist]
    return collapse(r_sum)


def _diff(
    regions_a: list[Region], regions_b: list[Region],
) -> list[Region]:
    result = []
    k = 0

    for reg_a in regions_a:
        if k >= len(regions_b):
            result.append(reg_a)
            continue
        if reg_a.chrom < regions_b[k].chrom:
            result.append(reg_a)
            continue
        if coalesce(reg_a.stop, MAX_POSITION) < \
                coalesce(regions_b[k].start, 1):
            result.append(reg_a)
            continue
        prev = coalesce(reg_a.start, 1)
        while k < len(regions_b) \
                and coalesce(regions_b[k].stop, MAX_POSITION) <= \
                coalesce(reg_a.stop, MAX_POSITION) \
                and regions_b[k].chrom == reg_a.chrom:
            if prev < coalesce(regions_b[k].start, 1):
                new_a = Region(
                    reg_a.chrom, prev,
                    coalesce(regions_b[k].start, 1) - 1)
                result.append(new_a)
            prev = coalesce(regions_b[k].stop, 1) + 1
            k += 1
        if k < len(regions_b) and regions_b[k].chrom != reg_a.chrom:
            continue
        if prev <= coalesce(reg_a.stop, MAX_POSITION):
            result.append(Region(reg_a.chrom, prev, reg_a.stop))

    return result


def difference(
    regions1: list[Region],
    regions2: list[Region], *,
    symmetric: bool = False,
) -> list[Region]:
    """Compute difference between two list of regions."""
    if not symmetric:
        left = collapse(regions1)
        left.sort(key=lambda x: (x.chrom, x.start))
    else:
        left = union(regions1, regions2)
        left.sort(key=lambda x: (x.chrom, x.start))

    right = intersection(regions1, regions2)

    return _diff(left, right)
