from __future__ import annotations
from collections import defaultdict
import copy

import pysam


def bedfile2regions(bed_filename):
    """Transform BED file into list of regions."""
    with open(bed_filename) as infile:
        regions = []
        for line in infile:
            if line[0] == "#":
                continue
            chrom, sbeg, send = line.strip().split("\t")
            beg = int(sbeg)
            end = int(send)
            regions.append(Region(chrom, beg + 1, end))
        return regions


def regions2bedfile(regions, bed_filename):
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
    while current_start < chrom_length:
        end = min(chrom_length, current_start + region_size)
        regions.append(Region(chrom, current_start, end))
        current_start = end

    return regions


def get_chromosome_length(
    tabix_file: pysam.TabixFile, chrom: str,
    step=100_000_000, precision=5_000_000
):
    """
    Return the length of a chromosome (or contig).

    Returned value is guarnteed to be larget than the actual contig length.
    """
    def any_records(riter):
        try:
            next(riter)
        except StopIteration:
            return False

        return True

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


class Region:
    """Class representing a genomic region."""

    # REGION_REGEXP2 = re.compile(
    #     r"^(chr)?(.+)(:([\d]{1,3}(,?[\d]{3})*)(-([\d]{1,3}(,?[\d]{3})*))?)?$"
    # )  # noqa

    def __init__(self, chrom=None, start=None, stop=None):

        self.chrom = chrom
        self.start = start
        self.stop = stop

    @property
    def begin(self):
        return self.start

    @property
    def end(self):
        return self.stop

    def __repr__(self):
        if self.start is None:
            return self.chrom
        if self.end is None:
            return f"{self.chrom}:{self.start}"
        return f"{self.chrom}:{self.start}-{self.stop}"

    def __hash__(self):
        return str(self).__hash__()

    def __eq__(self, other):
        return (
            self.chrom == other.chrom
            and self.start == other.start
            and self.stop == other.stop
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def isin(self, chrom, pos):
        """Check if a genomic position is insde of the region."""
        if chrom != self.chrom:
            return False

        if self.start and pos < self.start:
            return False
        if self.stop and pos > self.stop:
            return False
        return True

    def intersection(self, other: Region):
        """Return intersection of the region with other region."""
        if self.chrom != other.chrom:
            return None
        if self.start > other.stop:
            return None
        if other.start > self.stop:
            return None
        start = max(self.start, other.start)
        stop = min(self.stop, other.stop)
        if start > stop:
            return None
        return Region(self.chrom, start, stop)

    def contains(self, other):
        return self.chrom == other.chrom and self.start <= other.start \
            and other.stop <= self.stop

    def len(self):
        return self.stop - self.start + 1

    @classmethod
    def from_str(cls, region):
        """Parse string representation of a region."""
        parts = [p.strip() for p in region.split(":")]
        if len(parts) == 1:
            return Region(parts[0], None, None)
        if len(parts) == 2:
            chrom = parts[0]
            parts = [p.strip() for p in parts[1].split("-")]
            start = int(parts[0].replace(",", ""))
            if len(parts) == 1:
                return Region(chrom, start, start)
            if len(parts) == 2:
                stop = int(parts[1].replace(",", ""))
                return Region(chrom, start, stop)
        return None

        # m = cls.REGION_REGEXP2.match(region_str)
        # if not m:
        #     return None
        # prefix, chrom, start, end = (
        #     m.group(1),
        #     m.group(2),
        #     m.group(3),
        #     m.group(6),
        # )
        # print(prefix, chrom, start, end)

        # if start:
        #     start = int(start.replace(",", ""))
        # if not end:
        #     end = start
        # else:
        #     end = int(end.replace(",", ""))

        # if start and end and start > end:
        #     return None

        # if prefix:
        #     return f"{prefix}{chrom}", start, end
        # else:
        #     return chrom, start, end

    # @staticmethod
    # def from_str(region_str):
    #     if region_str is None:
    #         return None
    #     parsed = Region.parse_str(region_str)
    #     if not parsed:
    #         return None

    #     chromosome, start, end = parsed

    #     return Region(chromosome, start, end)


def all_regions_from_chrom(regions, chrom):
    """Subset of regions in R that are from chr."""
    return [r for r in regions if r.chrom == chrom]


def unique_regions(regions):
    """Remove duplicated regions."""
    return list(set(regions))


def connected_component(regions):
    """Return connected component of regions.

    This might be the same as collapse.
    """
    import networkx as nx  # pylint: disable=import-outside-toplevel

    graph = nx.Graph()

    graph.add_nodes_from(regions)
    regions_by_chrom = defaultdict(list)
    for reg in regions:
        regions_by_chrom[reg.chrom].append(reg)

    for _chrom, nds in regions_by_chrom.items():
        nds.sort(key=lambda x: x.stop)  # type: ignore
        for k in range(1, len(nds)):
            for j in range(k - 1, -1, -1):
                if nds[k].start <= nds[j].stop:
                    graph.add_edge(nds[k], nds[j])
                else:
                    break
    return nx.connected_components(graph)


def collapse(source, is_sorted=False):
    """Collapse list of regions."""
    if not source:
        return source

    regions = copy.deepcopy(source)

    if not is_sorted:
        regions.sort(key=lambda x: x.start)

    collapsed = defaultdict(list)

    collapsed[regions[0].chrom].append(regions[0])

    for reg in regions[1:]:
        chrom_collapsed = collapsed.get(reg.chrom)
        if not chrom_collapsed:
            collapsed[reg.chrom].append(reg)
            continue
        prev_reg = chrom_collapsed[-1]

        if reg.start <= prev_reg.stop:
            if reg.stop > prev_reg.stop:
                collapsed[reg.chrom][-1].stop = reg.stop
            continue

        collapsed[reg.chrom].append(reg)

    result = []
    for v in list(collapsed.values()):
        result.extend(v)
    return result


def collapse_no_chrom(source, is_sorted=False):
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
                prev_reg.stop = reg.stop
            continue

        collapsed.append(reg)

    return collapsed


def total_length(regions):
    return sum(regions.len() for x in regions)


def intersection(regions1, regions2):
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
                new_i = copy.copy(i)
                new_i.start = s1_c[k].start
                intersect.append(new_i)
                break
            if i.start > s1_c[k].start:
                if i.stop <= s1_c[k].stop:
                    intersect.append(i)
                    break
                new_i = copy.copy(i)
                new_i.stop = s1_c[k].stop
                intersect.append(new_i)
                k += 1
                continue

    return intersect


def union(*r):
    """Collapse many lists of regions."""
    r_sum = [el for list in r for el in list]
    return collapse(r_sum)


def _diff(regions_a, regions_b):
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
                new_a = Region(reg_a.chrom, prev, regions_b[k].start - 1)
                result.append(new_a)
            prev = regions_b[k].stop + 1
            k += 1
        if k < len(regions_b) and regions_b[k].chrom != reg_a.chrom:
            continue
        if prev <= reg_a.stop:
            result.append(Region(reg_a.chrom, prev, reg_a.stop))

    return result


def difference(regions1, regions2, symmetric=False):
    """Compute difference between two list of regions."""
    if not symmetric:
        left = collapse(regions1)
        left.sort(key=lambda x: (x.chrom, x.start))
    else:
        left = union(regions1, regions2)
        left.sort(key=lambda x: (x.chrom, x.start))

    right = intersection(regions1, regions2)

    return _diff(left, right)
