from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Optional, Union, Iterator, Sequence
import logging

import pysam
import networkx as nx

logger = logging.getLogger(__name__)


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
    with open(bed_filename, "w") as outfile:
        for reg in regions:
            outfile.write(
                f"{reg.chrom}\t{reg.start-1}\t{reg.stop}\n")


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
    step: int = 100_000_000, precision: int = 5_000_000
) -> Optional[int]:
    """
    Return the length of a chromosome (or contig).

    Returned value is guarnteed to be larget than the actual contig length.
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
        return right

    except ValueError as ex:
        logger.warning(
            "unable to find length of contig %s: %s", chrom, ex)
        return None


class Region:
    """Class representing a genomic region."""

    def __init__(
        self, chrom: str,
        start: Optional[int] = None, stop: Optional[int] = None
    ):
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
            and self.stop == other.stop
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def isin(self, chrom: str, pos: int) -> bool:
        """Check if a genomic position is insde of the region."""
        if chrom != self.chrom:
            return False

        if self.start and pos < self.start:
            return False
        if self.stop and pos > self.stop:
            return False
        return True

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
        chrom: str, start: Optional[int], stop: Optional[int]
    ) -> Optional[Region]:
        if chrom is None:
            return None
        if start is not None and stop is not None:
            if start > stop:
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

        assert self.start is not None and self.stop is not None
        return self._make_region(
            self.chrom,
            self._max(self.start, other.start),
            self._min(self.stop, other.stop)
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

        assert self.start is not None and self.stop is not None
        if other.stop is None or other.start is None:
            return False
        return self.start <= other.start \
            and other.stop <= self.stop

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
        start: int, stop: int
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

    for _chrom, nds in regions_by_chrom.items():
        nds.sort(key=lambda x: x.stop)
        for k in range(1, len(nds)):
            for j in range(k - 1, -1, -1):
                if nds[k].start <= nds[j].stop:
                    graph.add_edge(nds[k], nds[j])
                else:
                    break
    return nx.connected_components(graph)


def collapse(
    source: Sequence[BedRegion],
    is_sorted: bool = False
) -> list[BedRegion]:
    """Collapse list of regions."""
    if not source:
        return list(source)

    regions = copy.deepcopy(list(source))

    if not is_sorted:
        regions.sort(key=lambda x: x.start)

    collapsed: dict[str, list[BedRegion]] = defaultdict(list)

    collapsed[regions[0].chrom].append(regions[0])

    for reg in regions[1:]:
        chrom_collapsed = collapsed.get(reg.chrom)
        if not chrom_collapsed:
            collapsed[reg.chrom].append(reg)
            continue
        prev_reg = chrom_collapsed[-1]

        if reg.start <= prev_reg.stop:
            if reg.stop > prev_reg.stop:
                last = collapsed[reg.chrom][-1]
                collapsed[reg.chrom][-1] = \
                    BedRegion(last.chrom, last.start, reg.stop)
            continue

        collapsed[reg.chrom].append(reg)

    result = []
    for v in list(collapsed.values()):
        result.extend(v)
    return result


def collapse_no_chrom(
    source: list[BedRegion],
    is_sorted: bool = False
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
    return sum(len(regions) for x in regions)


def intersection(
    regions1: list[BedRegion], regions2: list[BedRegion]
) -> list[BedRegion]:
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
            if i.stop < s1_c[k].start:
                break
            if i.start > s1_c[k].stop:
                k += 1
                continue
            if i.start <= s1_c[k].start:
                if i.stop >= s1_c[k].stop:
                    intersect.append(s1_c[k])
                    k += 1
                    continue
                new_i = BedRegion(i.chrom, s1_c[k].start, i.stop)
                intersect.append(new_i)
                break
            if i.start > s1_c[k].start:
                if i.stop <= s1_c[k].stop:
                    intersect.append(i)
                    break
                new_i = BedRegion(i.chrom, i.start, s1_c[k].stop)
                intersect.append(new_i)
                k += 1
                continue

    return intersect


def union(*r: list[BedRegion]) -> list[BedRegion]:
    """Collapse many lists of regions."""
    r_sum = [el for list in r for el in list]
    return collapse(r_sum)


def _diff(
    regions_a: list[BedRegion], regions_b: list[BedRegion]
) -> list[BedRegion]:
    result = []
    k = 0

    for reg_a in regions_a:
        if k >= len(regions_b):
            result.append(reg_a)
            continue
        if reg_a.chrom < regions_b[k].chrom:
            result.append(reg_a)
            continue
        if reg_a.stop < regions_b[k].start:
            result.append(reg_a)
            continue
        prev = reg_a.start
        while k < len(regions_b) \
                and regions_b[k].stop <= reg_a.stop \
                and regions_b[k].chrom == reg_a.chrom:
            if prev < regions_b[k].start:
                new_a = BedRegion(reg_a.chrom, prev, regions_b[k].start - 1)
                result.append(new_a)
            prev = regions_b[k].stop + 1
            k += 1
        if k < len(regions_b) and regions_b[k].chrom != reg_a.chrom:
            continue
        if prev <= reg_a.stop:
            result.append(BedRegion(reg_a.chrom, prev, reg_a.stop))

    return result


def difference(
    regions1: list[BedRegion], regions2: list[BedRegion],
    symmetric: bool = False
) -> list[BedRegion]:
    """Compute difference between two list of regions."""
    if not symmetric:
        left = collapse(regions1)
        left.sort(key=lambda x: (x.chrom, x.start))
    else:
        left = union(regions1, regions2)
        left.sort(key=lambda x: (x.chrom, x.start))

    right = intersection(regions1, regions2)

    return _diff(left, right)
