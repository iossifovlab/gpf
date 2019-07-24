#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from builtins import range
from past.utils import old_div
from builtins import object
import os
import sys
import gzip
import numpy
from collections import namedtuple


# imitate VariantRecord for many files
def RefAltsIndex(ra):
    r = sorted(list(set([x[0] for x in ra])))
    ref = r[-1]  # longest one is new ref
    # assume that all the "r" start with the same as "ref"

    alts = []
    nIdx = {}
    for r, a in ra:
        s = ref[len(r):]
        an = [x+s for x in a]  # new alternative

        nIdx[(r, a)] = an
        alts += an

    alts = tuple(set(alts))
    # print nIdx
    iAlt = {}
    for k, v in list(nIdx.items()):
        ix = [0] + [alts.index(a)+1 for a in v]
        # print k,v,alts,ix
        iAlt[k] = numpy.array(ix)  # (lambda x: tuple( [ix[n] for n in x] ) )
    # if r[0] != r[-1]: print 'Note >', ra, 'OUT >', ref, alts, iAlt;
    return ref, alts, iAlt


# ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
# ##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Genotype Quality,
#   the Phred-scaled marginal (or unconditional) probability of the called
#   genotype">
# ##FORMAT=<ID=GL,Number=G,Type=Float,Description="Genotype Likelihood,
#   log10-scaled likelihoods of the data given the called genotype for each
#   possible genotype generated from the reference and alternate alleles given
#   the sample ploidy">
# ##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
# ##FORMAT=<ID=RO,Number=1,Type=Integer,Description="Reference allele
#   observation count">
# ##FORMAT=<ID=QR,Number=1,Type=Integer,Description="Sum of quality of the
#   reference observations">
# ##FORMAT=<ID=AO,Number=A,Type=Integer,Description="Alternate allele
#   observation count">
# ##FORMAT=<ID=QA,Number=A,Type=Integer,Description="Sum of quality of the
#   alternate observations">
#
# [('GT', (0, 0)), ('AD', (8, 0)), ('DP', 8), ('GQ', 0), ('PL', (0, 0, 234))]
#   genotype                       read depth  GT qual
def getGQ(dx):
    try:
        return list(dx['GQ'])
    except TypeError:
        return [dx['GQ']]
    except KeyError:
        if ('QR' in dx) and ('QA' in dx):
            return [dx['QR']] + list(dx['QA'])
        else:
            return []


def getCount(sx):
    # special case of modified counts
    if 'CNT' in sx:
        return sx['CNT']

    if ('RO' in sx) and ('AO' in sx):
        return [sx['RO']] + list(sx['AO'])

    if 'AD' in sx:
        return list(sx['AD'])

    if ('NR' in sx) and ('NV' in sx):
        # NR Number of reads covering variant location in this sample
        # NV Number of reads containing variant in this sample
        # print data.ref, data.alts, dx['GT'], dx['NR'], dx['NV']
        if len(sx['NR']) == 1 and len(sx['NV']) == 1:
            return [sx['NR'][0] - sx['NV'][0], sx['NV'][0]]
        # the other cases are difficult to figure out what those numbers
        # ar mean

    return []


# nIx: new Index of Alt, created by RefAltsIndex()
# sx: sample info, such as genotype
# alts: alts at the site (not the same as the original "sx"
def modifyData(nIx, sx, alts):
    if None in sx['GT']:
        return sx

    cnt = numpy.zeros((len(alts)+1,), dtype=int) - 1
    # default for no info
    cx = numpy.array(getCount(sx), dtype=int)
    if len(cx) == len(nIx):
        cnt[nIx] = cx

    sample = dict(sx)
    sample['GT'] = tuple(list(nIx[list(sx['GT'])]))
    sample['CNT'] = list(cnt)
    # print alts, nIx, sample
    return sample


VrtRcrd2 = namedtuple(
    'VariantRecord', 'chrom,pos,ref,alts,samples'.split(','))


# RX is array of pysam.VariantFile.VariantRecord
def universalRefAlt(RX, sI, missingInfoAsRef=True):
    if len(RX) == 1:
        return RX[0]

    chrom = tuple(set([rx.chrom for rx in RX if rx is not None]))
    pos = tuple(set([rx.pos for rx in RX if rx is not None]))

    ra = list(set([(rx.ref, rx.alts) for rx in RX if rx is not None]))

    samples = {}

    if len(ra) == 1:  # simplest case
        for s, i in list(sI.items()):
            try:
                samples[s] = dict(RX[i].samples[s])
            except AttributeError:
                if missingInfoAsRef:
                    samples[s] = {'GT': (0, 0)}
                else:
                    samples[s] = {'GT': (None, None)}
                    # default and only supplies GT

        ra = ra[0]
        return VrtRcrd2(*[chrom[0], pos[0], ra[0], ra[1], samples])

    else:
        # general case (ref1,ref2), alt1, alt2
        # only change genotype index
        ref, alts, iAlt = RefAltsIndex(ra)

        for s, i in list(sI.items()):
            try:
                idx = (RX[i].ref, RX[i].alts)
                sx = RX[i].samples[s]
                # sx['GT'] = tuple( iAlt[idx][ list(sx['GT']) ] )
                # Done by modifyData
                samples[s] = modifyData(iAlt[idx], sx, alts)
            except AttributeError:
                if missingInfoAsRef:
                    samples[s] = {'GT': (0, 0)}
                else:
                    samples[s] = {'GT': (None, None)}
                    # default and only supplies GT

        ra = ra[0]
        return VrtRcrd2(*[chrom[0], pos[0], ref, alts, samples])


def procFileNames(fNames):
    if isinstance(fNames, list):
        return fNames

    if not fNames.endswith('.txt'):
        return fNames.split(',')

    with open(fNames) as lfile:
        fNS = [line.strip('\n') for line in lfile]
        return fNS


class Reader(object):
    def __init__(self, fname=None):
        self.fname = fname
        try:
            if not fname:
                return

            if fname.endswith('.gz') or fname.endswith('.bgz'):
                self.file = gzip.open(fname, 'rb')
            else:
                self.file = open(fname, 'r')
        except IOError:
            pass

    def exists(self):
        try:
            self.file
            return True
        except AttributeError:
            return False

    def notExistExit(self):
        try:
            self.file
        except AttributeError:
            print(self.fname + ' not exist')
            exit(1)

    def readline(self):
        return self.file.readline()

    def __next__(self):
        line = self.readline()

        if not line:
            raise StopIteration()
        return line

    def __iter__(self):
        return self


class ReaderStat(Reader):
    def __init__(self, fname=None):
        Reader.__init__(self, fname)

        if not self.exists():
            return

        self.head = self.file.readline().strip('\n')
        hdr = self.head.split('\t')
        self.dct = dict((hdr[n], n) for n in range(len(hdr)))

        self.idxID = [
            self.dct['chr'], self.dct['position'], self.dct['variant']
        ]

        line = self.file.readline()
        if line == '':
            return

        self.cLine = line.strip('\n')
        self.cTerms = self.cLine.split('\t')
        self.cID = ':'.join([self.cTerms[n] for n in self.idxID])

    def readLine(self):
        while self.file:
            self.cLine = self.file.readline().strip('\n')
            if len(self.cLine) < 1 or self.cLine[0] != '#':
                break

        if self.cLine == '' or not self.file:
            self.cLine = ''
            self.cTerm = []
            self.cId = ''
            return False

        self.cTerms = self.cLine.split('\t')
        self.cID = ':'.join([self.cTerms[n] for n in self.idxID])
        return True

    def getFamilyData(self):
        return self.cTerms[self.dct['familyData']]

    def getStat(self):
        v = [
            int(self.cTerms[self.dct[x]])
            for x in ['all.nParCalled', 'all.nAltAlls']
        ]
        w = [
            old_div(float(self.cTerms[self.dct[x]]), 100.)
            for x in ['all.prcntParCalled', 'all.altFreq']
        ]

        return v, w


class Writer(object):
    def __init__(self, fname=None):
        self.bgzFlag = False

        if not fname:
            self.file = sys.stdout
        else:
            if fname.endswith('.bgz'):
                self.bgzFlag = True

                terms = fname.split('.')
                self.filename = '.'.join(terms[0:(len(terms)-1)])
                self.file = open(self.filename, 'w')
            elif fname.endswith('.gz'):
                self.file = gzip.open(fname, 'wb')
            else:
                self.file = open(fname, 'w')

    def __del__(self):
        if not self.bgzFlag:
            return

        self.file.close()
        try:
            fname = self.filename
            os.system(
                'bgzip ' + fname + '; mv ' + fname + '.gz ' +
                fname + '.bgz')  # self.filename+'.bgz' )
        except IOError as e:
            print(e)

    def write(self, xstr):
        self.file.write(xstr)


def tooManyFile(xstr):
    if xstr.endswith('.txt.gz') or xstr.endswith('.txt.bgz'):
        xloc = 3
    else:
        xloc = 2

    terms = xstr.split('.')
    terms[len(terms)-xloc] += '-TOOMANY'

    return '.'.join(terms)


# def main():
#      fnames =  'FB.149.vcf.gz,PL.148.vcf.gz,JHC.147.vcf.gz'
#      vfs = vcfFiles( fnames )

#      for rx in vfs:
#         #print rx.chrom, rx.pos, rx.ref, rx.alts
#         pass

#      '''
#      vfs.setRegion('X')

#      flag = False
#      for rx in vfs:
#         if flag: continue

#         print '##', rx.chrom, rx.pos, rx.ref, rx.alts
#         flag = True
#      print '##', rx.chrom, rx.pos, rx.ref, rx.alts
#      flag = False
#      for rx in vfs.fetch('X'):
#         if flag: continue

#         print '$$', rx.chrom, rx.pos, rx.ref, rx.alts
#         flag = True
#      print '$$', rx.chrom, rx.pos, rx.ref, rx.alts
#      '''
# if __name__ == "__main__":
#    main()
