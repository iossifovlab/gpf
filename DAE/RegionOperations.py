#!/bin/env python

# version 2.1
# January/16th/2014
# written by Ewa

from __future__ import unicode_literals
from builtins import str
from builtins import range
from builtins import object
from collections import namedtuple
from collections import defaultdict
import copy
import re


def bedFile2Rgns(bedFN):
    F = open(bedFN)
    r = []
    for l in F:
        if l[0] == '#':
            continue
        chrom, beg, end = l.strip().split("\t")
        beg = int(beg)
        end = int(end)
        r.append(Region(chrom, beg + 1, end))
    F.close()
    return r


def rgns2BedFile(rgns, bedFN):
    F = open(bedFN, "w")
    for rr in rgns:
        F.write("%s\t%d\t%d\n" % (rr.chr, rr.start - 1, rr.stop))
    F.close()


class Region(object):
    REGION_REGEXP2 = re.compile(
        "^(chr)?(\d+|[Xx]):([\d]{1,3}(,?[\d]{3})*)"
        "(-([\d]{1,3}(,?[\d]{3})*))?$")

    def __init__(self, chr, start, stop):
        self.chr = chr
        self.start = start
        self.stop = stop

    def __repr__(self):
        return "Region(" + self.chr + "," + \
            str(self.start) + "," + str(self.stop) + ")"

    def __str__(self):
        return self.chr + ":" + str(self.start) + "-" + str(self.stop)

    def __hash__(self):
        return str(self).__hash__()

    def __eq__(self, other):
        return self.chr == other.chr and \
            self.start == other.start and self.stop == other.stop

    def __ne__(self, other):
        return not self.__eq__(other)

    def len(self):
        return self.stop - self.start + 1

    @classmethod
    def parse_str(cls, region_str):
        m = cls.REGION_REGEXP2.match(region_str)
        if not m:
            return None
        chrome, start, end = m.group(2), m.group(3), m.group(6)
        if not start:
            return None
        start = int(start.replace(',', ''))
        if not end:
            end = start
        else:
            end = int(end.replace(',', ''))

        if start > end:
            return None
        return chrome, start, end

    @staticmethod
    def from_str(region_str):
        parsed = Region.parse_str(region_str)
        if not parsed:
            return None

        chromosome, start, end = parsed

        return Region(chromosome, start, end)



def all_regions_from_chr(R, chrom):
    """Subset of regions in R that are from chr."""
    A = [r for r in R if r.chr == chrom]
    return A


def unique_regions(R):
    """removed duplicated regions"""

    return list(set(R))


def connected_component(R):
    """This might be the same as collapse"""

    import networkx as nx

    Un_R = unique_regions(R)

    G = nx.Graph()

    G.add_nodes_from(R)
    D = defaultdict(list)
    for r in R:
        D[r.chr].append(r)


    for chr, nds in list(D.items()):
        nds.sort(key=lambda x: x.stop)
        for k in range(1, len(nds)):
            for j in range(k - 1,-1,-1):
                if nds[k].start <= nds[j].stop:
                    G.add_edge(nds[k], nds[j])
                else:
                    break
    CC = nx.connected_components(G)
    return(CC)


def collapse(r, is_sorted=False):
    """Ivan knows"""

    if not r:
        return r

    r_copy = copy.deepcopy(r)

    if is_sorted == False:
        r_copy.sort(key=lambda x: x.start)

    C = defaultdict(list)

    C[r_copy[0].chr].append(r_copy[0])

    for i in r_copy[1:]:
        try:
            j = C[i.chr][-1]
        except:
            C[i.chr].append(i)
            continue

        if i.start <= j.stop:
            if i.stop > j.stop:
                C[i.chr][-1].stop = i.stop
            continue

        C[i.chr].append(i)

    L = []
    for v in list(C.values()):
        L.extend(v)
        

    return L



def collapse_noChr(r, is_sorted=False):
    """collapse by ignoring the chromosome. Useful when the caller knows that all the regions are from the same chromosome."""
   
    if r == []:

        return r
    r_copy = copy.copy(r)

    if is_sorted == False:
        r_copy.sort(key=lambda x: x.start)

    C = [r_copy[0]]
    for i in r_copy[1:]:
        j = C[-1]
        if i.start <= j.stop:
            if i.stop > j.stop:
                C[-1].stop = i.stop
            continue

        C.append(i)

    return C


def totalLen(s):
    return sum(x.len() for x in s)


def intersection(s1, s2):
    """ First collapses each for lists of regions s1 and s2 and then find the intersection. """
    s1_c = collapse(s1)
    s2_c = collapse(s2)
    s1_c.sort(key=lambda x: (x.chr, x.start))
    s2_c.sort(key=lambda x: (x.chr, x.start))

    I = []

    k = 0

    for i in s2_c:
        while k < len(s1_c):
            if i.chr != s1_c[k].chr:
                if i.chr > s1_c[k].chr:
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
                    I.append(s1_c[k])
                    k += 1
                    continue
                new_i = copy.copy(i)
                new_i.start = s1_c[k].start
                I.append(new_i)
                break
            if i.start > s1_c[k].start:
                if i.stop <= s1_c[k].stop:
                    I.append(i)
                    break
                new_i = copy.copy(i)
                new_i.stop = s1_c[k].stop
                I.append(new_i)
                k += 1
                continue

    return(I)


def union(*r):
    """Collapses many lists"""
    r_sum = [el for list in r for el in list]
    return(collapse(r_sum))


def _diff(A, B):
    D = []
    k = 0

    for a in A:
        if k >= len(B):
            D.append(a)
            continue
        if a.chr < B[k].chr:
            D.append(a)
            continue
        if a.stop < B[k].start:
            D.append(a)
            continue
        prev = a.start
        while k < len(B) and B[k].stop <= a.stop and B[k].chr == a.chr:
            if prev < B[k].start:
                new_a = Region(a.chr, prev, B[k].start - 1)
                D.append(new_a)
            prev = B[k].stop + 1
            k += 1
        if k < len(B) and B[k].chr != a.chr:
            continue
        if prev <= a.stop:
            D.append(Region(a.chr, prev, a.stop))

    return(D)


def difference(s1, s2, symmetric=False):

    if symmetric == False:
        A = collapse(s1)
        A.sort(key=lambda x: (x.chr, x.start))
    else:
        A = union(s1, s2)
        A.sort(key=lambda x: (x.chr, x.start))

    B = intersection(s1, s2)

    D = _diff(A, B)

    return(D)
