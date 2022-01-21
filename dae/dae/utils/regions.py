#!/bin/env python

# version 2.1
# January/16th/2014
# written by Ewa

from collections import defaultdict
import copy


def bedfile2regions(bed_filename):
    with open(bed_filename) as infile:
        regions = []
        for line in infile:
            if line[0] == "#":
                continue
            chrom, beg, end = line.strip().split("\t")
            beg = int(beg)
            end = int(end)
            regions.append(Region(chrom, beg + 1, end))
        return regions


def regions2bedfile(regions, bed_filename):
    with open(bed_filename, "w") as outfile:
        for reg in regions:
            outfile.write(
                f"{reg.chrom}\t{reg.start-1}\t{reg.stop}\n")


class Region(object):

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
        elif self.end is None:
            return "{}:{}".format(self.chrom, self.start)
        else:
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
        if chrom != self.chrom:
            return False

        if self.start and pos < self.start:
            return False
        if self.stop and pos > self.stop:
            return False
        return True

    def intersection(self, other):
        if self.chrom != other.chrom:
            return None
        if self.start > other.stop:
            return None
        if other.start > self.stop:
            return None
        start = max(self.start, other.start)
        stop = min(self.stop, other.stop)
        if start >= stop:
            return None
        return Region(self.chrom, start, stop)

    def contains(self, other):
        return self.chrom == other.chrom and self.start <= other.start \
            and other.stop <= self.stop

    def len(self):
        return self.stop - self.start + 1

    @classmethod
    def from_str(cls, region):
        parts = [p.strip() for p in region.split(":")]
        if len(parts) == 1:
            return Region(parts[0], None, None)
        elif len(parts) == 2:
            chrom = parts[0]
            parts = [p.strip() for p in parts[1].split("-")]
            start = int(parts[0].replace(",", ""))
            if len(parts) == 1:
                return Region(chrom, start, start)
            elif len(parts) == 2:
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


def all_regions_from_chr(R, chrom):
    """Subset of regions in R that are from chr."""
    A = [r for r in R if r.chrom == chrom]
    return A


def unique_regions(R):
    """removed duplicated regions"""
    return list(set(R))


def connected_component(R):
    """This might be the same as collapse"""
    import networkx as nx  # type: ignore

    G = nx.Graph()

    G.add_nodes_from(R)
    D = defaultdict(list)
    for r in R:
        D[r.chrom].append(r)

    for _chrom, nds in list(D.items()):
        nds.sort(key=lambda x: x.stop)
        for k in range(1, len(nds)):
            for j in range(k - 1, -1, -1):
                if nds[k].start <= nds[j].stop:
                    G.add_edge(nds[k], nds[j])
                else:
                    break
    CC = nx.connected_components(G)
    return CC


def collapse(source, is_sorted=False):
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
        else:
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
    """collapse by ignoring the chromosome. Useful when the caller knows
    that all the regions are from the same chromosome."""

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


def totalLen(s):
    return sum(x.len() for x in s)


def intersection(s1, s2):
    """ First collapses each for lists of regions s1 and s2 and then find
    the intersection. """
    s1_c = collapse(s1)
    s2_c = collapse(s2)
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
    """Collapses many lists"""
    r_sum = [el for list in r for el in list]
    return collapse(r_sum)


def _diff(A, B):
    D = []
    k = 0

    for a in A:
        if k >= len(B):
            D.append(a)
            continue
        if a.chrom < B[k].chrom:
            D.append(a)
            continue
        if a.stop < B[k].start:
            D.append(a)
            continue
        prev = a.start
        while k < len(B) and B[k].stop <= a.stop and B[k].chrom == a.chrom:
            if prev < B[k].start:
                new_a = Region(a.chrom, prev, B[k].start - 1)
                D.append(new_a)
            prev = B[k].stop + 1
            k += 1
        if k < len(B) and B[k].chrom != a.chrom:
            continue
        if prev <= a.stop:
            D.append(Region(a.chrom, prev, a.stop))

    return D


def difference(s1, s2, symmetric=False):

    if not symmetric:
        A = collapse(s1)
        A.sort(key=lambda x: (x.chrom, x.start))
    else:
        A = union(s1, s2)
        A.sort(key=lambda x: (x.chrom, x.start))

    B = intersection(s1, s2)

    D = _diff(A, B)

    return D
