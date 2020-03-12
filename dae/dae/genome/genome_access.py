#!/bin/env python

# June 6th 2013
# by Ewa

import sys
import os

from typing import List

from dae.utils.regions import Region


class GenomicSequence(object):
    def __init__(self):
        self.genomic_file = None
        self.genomic_index_file = None
        self.chromosomes = None
        self.pseudo_autosomal_regions = None
        self._indexing = {}

    def __create_index_file(self, file):
        from pysam import faidx

        faidx(file)

    def __chromNames(self):
        with open(self.genomic_index_file) as infile:
            chroms = []

            while True:
                line = infile.readline()
                if not line:
                    break
                line = line.split()
                chroms.append(line[0])

        self.chromosomes = chroms

    def __initiate(self):
        self._indexing = {}
        f = open(self.genomic_index_file, "r")
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            self._indexing[line[0]] = {
                "length": int(line[1]),
                "startBit": int(line[2]),
                "seqLineLength": int(line[3]),
                "lineLength": int(line[4]),
            }
        f.close()

        self.__f = open(self.genomic_file, "r")

    def close(self):
        self.__f.close()

    def _load_genome(self, file):
        if not os.path.exists(file + ".fai"):
            self.__create_index_file(file)

        self.genomic_index_file = file + ".fai"
        self.genomic_file = file
        self.__chromNames()
        self.__initiate()

        return self

    def get_chr_length(self, chrom):

        try:
            return self._indexing[chrom]["length"]
        except KeyError:
            print("Unknown chromosome!", chrom, file=sys.stderr)

    def get_all_chr_lengths(self):
        result = []
        for chrom in self.chromosomes:
            result.append((chrom, self._indexing[chrom]["length"]))
        return result

    def get_sequence(self, chrom, start, stop):
        if chrom not in self.chromosomes:
            print("Unknown chromosome!", chrom, file=sys.stderr)
            return -1

        self.__f.seek(
            self._indexing[chrom]["startBit"]
            + start
            - 1
            + (start - 1) / self._indexing[chrom]["seqLineLength"]
        )

        ll = stop - start + 1
        x = 1 + ll // self._indexing[chrom]["seqLineLength"]

        w = self.__f.read(ll + x)
        w = w.replace("\n", "")[:ll]

        return w.upper()

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        # TODO Handle variants which are both inside and outside a PAR
        # Currently, if the position of the reference is within a PAR,
        # the whole variant is considered to be within an autosomal region
        def in_any_region(chrom: str, pos: int, regions: List[Region]) -> bool:
            return any(map(lambda x: x.isin(chrom, pos), regions))

        chrom = chrom.replace("chr", "")
        if chrom == "X":
            return in_any_region(
                chrom, pos, self.pseudo_autosomal_regions.X  # type: ignore
            )
        elif chrom == "Y":
            return in_any_region(
                chrom, pos, self.pseudo_autosomal_regions.Y  # type: ignore
            )
        else:
            return False


def openRef(filename):
    assert os.path.exists(filename), filename
    assert filename.endswith(".fa")

    g_a = GenomicSequence()
    return g_a._load_genome(filename)
