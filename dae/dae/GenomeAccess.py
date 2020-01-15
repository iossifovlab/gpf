#!/bin/env python

# June 6th 2013
# by Ewa

import sys
import os


class GenomicSequence_Ivan(object):

    genomicFile = None
    genomicIndexFile = None
    allChromosomes = None
    pseudo_autosomal_regions = None

    def __createIndexFile(self, file):
        from pysam import faidx
        faidx(file)

    def __chromNames(self):
        file = open(self.genomicIndexFile)
        Chr = []

        while True:
            line = file.readline()
            if not line:
                break
            line = line.split()
            Chr.append(line[0])

        file.close()
        self.allChromosomes = Chr

    def __initiate(self):
        self._Indexing = {}
        f = open(self.genomicIndexFile, 'r')
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            self._Indexing[line[0]] = {
                'length': int(line[1]),
                'startBit': int(line[2]),
                'seqLineLength': int(line[3]),
                'lineLength': int(line[4])
            }
        f.close()

        self.__f = open(self.genomicFile, 'r')

    def close(self):
        self.__f.close()

    def _load_genome(self, file):
        if not os.path.exists(file + ".fai"):
            self.__createIndexFile(file)

        self.genomicIndexFile = file + ".fai"
        self.genomicFile = file
        self.__chromNames()
        self.__initiate()

        return(self)

    def get_chr_length(self, chrom):

        try:
            return(self._Indexing[chrom]['length'])
        except KeyError:
            print("Unknown chromosome!", chrom, file=sys.stderr)

    def get_all_chr_lengths(self):
        R = []
        for chrom in self.allChromosomes:
            R.append((chrom, self._Indexing[chrom]['length']))
        return(R)

    def getSequence(self, chrom, start, stop):
        if chrom not in self.allChromosomes:
            print("Unknown chromosome!", chrom, file=sys.stderr)
            return -1

        self.__f.seek(
            self._Indexing[chrom]['startBit'] + start - 1 +
            (start-1) / self._Indexing[chrom]['seqLineLength'])

        ll = stop-start+1
        x = 1 + ll // self._Indexing[chrom]['seqLineLength']

        w = self.__f.read(ll + x)
        w = w.replace("\n", "")[:ll]

        return w.upper()

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        # TODO Handle variants which are both inside and outside a PAR
        # Currently, if the position of the reference is within a PAR,
        # the whole variant is considered to be within an autosomal region
        chrom = chrom.replace('chr', '')
        return chrom == 'X' and \
            self.pseudo_autosomal_regions.x.region.isin(chrom, pos)


def openRef(filename):

    if not os.path.exists(filename):
        print("The input file: " + filename + " does NOT exist!",
              file=sys.stderr)
        sys.exit(-1)

    if filename.endswith('.fa'):
        # ivan's method
        g_a = GenomicSequence_Ivan()
        return(g_a._load_genome(filename))
    else:
        print("Unrecognizable format of the file: " + filename,
              file=sys.stderr)
        sys.exit(-1)
