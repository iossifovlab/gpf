#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import zip
from builtins import map
from builtins import str
from builtins import range
import optparse
import sys
import os
import pysam
import numpy
from collections import namedtuple, defaultdict, OrderedDict
from itertools import izip
import itertools

#from vcf2DAEutil import *
import variantFormat as vrtF
from ped2NucFam import *
import vrtIOutil as vIO


class IndividualVariant(object):
    def __init__(self, personId, family):
        self.id = personId
        self.family = family
        self.ref = True
        self._gt = None


class FamilyVariant:
    def __init__(self, familyInfo, altsCount):
        self.familyInfo = familyInfo
        self.incomplete = False
        self.individuals = dict()

        self._GT = None
        self._cnt = None
        self.altsCount = altsCount

    def _updateGT(self, individualId, n):
        GT = self._GT[n]
        if individualId in self.individuals:
            for ix in self.individuals[individualId].gt:
                    GT[ix] += 1
        else:
            GT[0] = 2

    def _updateCnt(self, data, individualId, n):
        if individualId in self.individuals:
            sample = self.individuals[individualId].sample
        else:
            sample = data.samples[individualId]
        cx = vIO.getCount(sample)

        if len(cx) == len(self.GT[n]):
            self.cnt[n] = cx

    def addSample(self, personId, sample, gt):
        if self.incomplete:
            return
        var = IndividualVariant(personId, self)
        var.sample = sample
        var.gt = gt
        self.individuals[personId] = var
    
    @property
    def GT(self):
        if self._GT is None:
            self._GT = numpy.zeros((len(self.familyInfo['ids']),
                                   self.altsCount,), dtype=numpy.int)
            for i, individualId in enumerate(self.familyInfo['ids']):
                self._updateGT(individualId, i)
        return self._GT

    @property
    def cnt(self):
        if self._cnt is None:
            self._cnt = numpy.zeros((len(self.familyInfo['ids']),
                                    self.altsCount,), dtype=numpy.int) - 1
            for i, individualId in enumerate(self.familyInfo['ids']):
                self._updateCnt(individualId, i)
        return self._cnt

    def fixCnt(self, data):
        self._cnt = numpy.zeros((len(self.familyInfo['ids']),
                                self.altsCount,), dtype=numpy.int) - 1
        for i, individualId in enumerate(self.familyInfo['ids']):
            self._updateCnt(data, individualId, i)

    def get_cnt_str(self, ix):
        return array2str(self.cnt, ix, delim=' ')


def generateFamilyVariants(data, fam, fInfo, individualToFamily):
    tlx = len(data.samples)
    clx = 0

    individuals = dict()
    interestingFamilies = dict()
    incomplete = set()
    altsCount = len(data.alts) + 1

    for k, v in data.samples.items():
        familyId = individualToFamily[k]

        gt = v['GT']

        if gt[0] is None:
            incomplete.add(familyId)
            continue

        interesting = False
        for a in gt:
            if a != 0:
                interesting = True
                break

        if interesting:
            if familyId not in interestingFamilies:
                familyInfo = fInfo[familyId]
                familyVariant = FamilyVariant(familyInfo, altsCount)
                interestingFamilies[familyId] = familyVariant
            else:
                familyVariant = interestingFamilies[familyId]

            familyVariant.addSample(k, v, gt)

        clx += 1

    filtered = [family for familyId, family in interestingFamilies.items()
                if familyId not in incomplete]

    count = len(fam) - len(incomplete)
    filtered.sort(key=lambda elem: elem.familyInfo['fid'])
    #print("generateFamilyVariants", len(fam), len(incomplete), len(interesting), len(samplesWithRef))

    return filtered, 100. * clx / tlx, count




# add more data on fam Info


def makeFamInfoConv(fInfo, pInfo):
    for k, v in fInfo.items():
        lx = len(v['ids'])
        sx = numpy.zeros((lx,), dtype=numpy.int)
        for n, mx in enumerate(v['newIds']):
            s = pInfo[mx].sex
            if s == '1':
                sx[n] = 1
        v['isMale'] = sx

        cl = len(v['famaIndex'])
        idxMF = numpy.zeros((cl, 3,), dtype=numpy.int)
        nC = range(lx)
        for n, (a, b) in enumerate(v['famaIndex'].items()):
            idxMF[n, :] = [a, b.fa, b.ma]
            nC.remove(a)
        v['iFM'] = idxMF
        v['notChild'] = numpy.array(nC)

    # print fInfo


def array2str(mx, ix, delim=''):
    n0, n1, n2 = mx[:, 0], mx[:, ix], mx.sum(1)
    n2 = n2 - n0 - n1

    s0 = map(str, n0)
    s1 = map(str, n1)
    s2 = map(str, n2)

    strx = delim.join(s0) + '/' + delim.join(s1)
    if sum(n2) > 0:
        strx += ('/' + delim.join(s2))

    return strx


def fixNonAutoX(familyVariant):  # fam, pInfo ):
    # Sex (1=male; 2=female; other=unknown)
    # assume [numFam]x[genotype count] and genotype are 0,1,2

    GT = familyVariant.GT
    isM = familyVariant.familyInfo['isMale']

    for n, im in enumerate(isM):
        if im == 0:
            continue  # female

        if sum(GT[n, :]) == 2 and sum(GT[n, :] == 1) > 0:
            return False
        else:
            GT[n, GT[n, :] == 2] = 1

    return True

# possible hap state
def hapState(cn):
    if cn == 0:
        return [0]
    if cn == 1:
        return [0, 1]

    return [1]


# mendel State
#
#(fa, ma, child) copy number
#       (ma,fa):(child) -- number of alleles
mStat = {  \
    # regular autosome 2 copies for all
    (2, 2, 2): {\
        (2, 2): [2],  (2, 1): [1, 2],  (2, 0): [1],  \
        (1, 2): [1, 2], (1, 1): [0, 1, 2], (1, 0): [0, 1],\
        (0, 2): [1],  (0, 1): [0, 1],  (0, 0): [0]},\
    # X and male child, only from ma
    (1, 2, 1): {\
        (1, 2): [1], (1, 1): [0, 1], (1, 0): [0],   \
        (0, 2): [1], (0, 1): [0, 1], (0, 0): [0]}, \
    # X and female child
    (1, 2, 2): {\
        (1, 2): [2], (1, 1): [1, 2], (1, 0): [1],  \
        (0, 2): [1], (0, 1): [0, 1], (0, 0): [0]}}

# primitive version of checking de-novo
# autosome


def isDenovo(familyVariant):  # fm : fa and ma index
    st = familyVariant.GT
    fm = familyVariant.familyInfo['iFM']

    assert sum(st.sum(1) != 2) == 0, 'copy number assume to be 2 for all'
    # mendel state for copy number 2 for all
    mdl = mStat[(2, 2, 2)]
    # all of them have ref state
    if sum(st[:, 0] != 2) == 0:
        return False

    for c, f, m in fm:  # fa ma child index
        for n, s in enumerate(st[c, :]):
            if s not in mdl[(st[f, n], st[m, n])]:
                # print st
                return True
            # print f,m,c,n,s, (st[f,n],st[m,n])

    return False


# fm : fa and ma index, isM: is Male array of 0 1(True)
def isDenovoNonAutosomalX(familyVariant):
    st = familyVariant.GT
    fm = familyVariant.familyInfo['iFM']
    isM = familyVariant.familyInfo['isMale']

    assert sum(st.sum(1) != (2 - isM)) == 0, 'copy number assume to be 2 for female, ' + \
        'and 1 for male male({:s}) copy({:s})'.format(
        ','.join(map(str, isM)), ','.join(['/'.join(map(str, s)) for s in st]))
    # mendel state for copy number, accordingly
    mdl = [mStat[(1, 2, 2)], mStat[(1, 2, 1)]]
    # all of them have ref state
    if sum(st[:, 0] != (2 - isM)) == 0:
        # print 'ref only', ','.join( ['/'.join(map(str,s)) for s in st] ), ','.join(map(str,isM))
        return False

    for c, f, m in fm:  # fa ma child index
        for n, s in enumerate(st[c, :]):
            if s not in mdl[isM[c]][(st[f, n], st[m, n])]:
                return True
            # print f,m,c,n,s, (st[f,n],st[m,n])

    return False

# output: dict[pos] = (out,str)
def printSome(output, pos=None, wsize=1000):
    if pos == None:
        for k in sorted(output.keys()):
            v = output[k]
            print >> v[0], v[1]

        output.clear()
        return

    dk = []
    for k in sorted(output.keys()):
        if k[0] > pos - wsize:
            break

        dk.append(k)
        v = output[k]
        print >> v[0], v[1]

    for k in dk:
        del output[k]


def famInVCF(fInfo, vcfs):
    fam = []
    for fid in sorted(fInfo.keys()):
        flag = False

        mm = []
        for sm in fInfo[fid]['ids']:
            if sm in vcfs:
                continue

            flag = True
            mm.append(sm)

        if flag:
            print >> sys.stderr, '\t'.join(
                ['family',  fid, 'notComplete', 'missing', ','.join(mm)])
            continue

        fam.append(fid)

    return fam



def main():
    # svip.ped
    #svip-FB-vars.vcf.gz, svip-PL-vars.vcf.gz, svip-JHC-vars.vcf.gz
    #pfile, dfile = 'data/svip.ped', 'data/svip-FB-vars.vcf.gz'
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-p", "--pedFile", dest="pedFile", default="data/svip.ped",
                      metavar="pedFile", help="pedigree file and family-name should be mother and father combination, not PED format")
    parser.add_option("-d", "--dataFile", dest="dataFile", default="data/svip-FB-vars.vcf.gz",
                      metavar="dataFile", help="VCF format variant file")

    parser.add_option("-x", "--project", dest="project", default="VIP",
                      metavar="project", help="project name [defualt:VIP")
    parser.add_option("-l", "--lab", dest="lab", default="SF",
                      metavar="lab", help="lab name [defualt:SF")

    parser.add_option("-o", "--outputPrefix", dest="outputPrefix", default="transmission",
                      metavar="outputPrefix", help="prefix of output transmission file")

    parser.add_option("-m", "--minPercentOfGenotypeSamples", dest="minPercentOfGenotypeSamples", type=float, default=25.,
                      metavar="minPercentOfGenotypeSamples", help="threshold percentage of gentyped samples to printout [default: 25]")
    parser.add_option("-t", "--tooManyThresholdFamilies", dest="tooManyThresholdFamilies", type=int, default=10,
                      metavar="tooManyThresholdFamilies", help="threshold for TOOMANY to printout [defaylt: 10]")

    parser.add_option("-s", "--missingInfoAsNone", action="store_true", dest="missingInfoAsNone", default=False,
                      metavar="missingInfoAsNone", help="missing sample Genotype will be filled with 'None' for many VCF files input")

    ox, args = parser.parse_args()
    pfile, dfile = ox.pedFile, ox.dataFile

    missingInfoAsRef = True
    if ox.missingInfoAsNone:
        missingInfoAsRef = False  # ; print NNN

    # print famFile
    # fInfo: each fam has mom, dad and child personal ID, old and new Ids
    # pInfo: each person has raw info from "PED" file
    fInfo, pInfo = procFamInfo(pfile)
    # add more info to fInfo such as
    #    notChild: who is not children
    #    iFM     : fa and ma index for each child in families
    #    isMale  : sex info in the order of ids and newIds (they have the same order)
    makeFamInfoConv(fInfo, pInfo)

    if os.path.isfile(ox.outputPrefix + '.txt'):
        print >> sys.stderr, ox.outputPrefix + '.txt: already exist'
        exit(1)

    # setup to print transmission files
    OUT = ox.outputPrefix + '.txt'
    TOOMANY = ox.outputPrefix + '-TOOMANY.txt'
    out = open(OUT, 'w')
    outTOOMANY = open(TOOMANY, 'w')

    print >> out, '\t'.join(
        'chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq'.split(','))
    print >> outTOOMANY, '\t'.join(
        'chr,position,variant,familyData'.split(','))

    #fam = [x for x in sorted(fInfo.keys())]
    #vf = pysam.VariantFile( dfile )
    vf = vIO.vcfFiles(dfile, missingInfoAsRef=missingInfoAsRef)
    fam = famInVCF(fInfo, vf)

    # print family Info in a format
    FAMOUT = ox.outputPrefix + '-families.txt'
    printFamData(fInfo, pInfo, proj=ox.project, lab=ox.lab,
                 listFam=fam, out=open(FAMOUT, 'w'))

    def digitP(x): return '{:.4f}'.format(x)
    cchr = ''
    output = {}

    individualToFamily = dict()

    for familyId in fam:
        familyInfo = fInfo[familyId]
        for personId in familyInfo['ids']:
            individualToFamily[personId] = familyId

    for rx in vf:
        familyVariants, pgt, count = generateFamilyVariants(rx, fam, fInfo,
                                                            individualToFamily)

        count2 = count - len(familyVariants)
        if pgt < ox.minPercentOfGenotypeSamples:
            continue
        #print >> sys.stderr, 'pcntg', pgt

        chrom = rx.chrom
        # callVariant( rx.pos, rx.ref, rx.alts )
        px, vx = vrtF.vcf2cshlFormat2(rx.pos, rx.ref, rx.alts)

        # print output and make it empty
        if cchr != chrom:
            printSome(output)
            cchr = chrom
        # reduce burden of computer memory
        if len(output) > 10000:
            printSome(output, pos=rx.pos)

        nonAutoX = False
        if chrom == 'X' and (not vrtF.isPseudoAutosomalX(px[0])):
            nonAutoX = True

        dx = []
        # save ok families, check whether autosomal or de novo
        for familyVariant in familyVariants:
            familyVariant.fixCnt(rx)
            if nonAutoX:
                # fInfo[fid]['ids'], pInfo )
                flag = fixNonAutoX(familyVariant)
                if not flag:
                    count -= 1
                    continue  # fail to fix

                flag = isDenovoNonAutosomalX(familyVariant)
                if flag:
                    count -= 1
                    continue  # denovo
            else:
                flag = isDenovo(familyVariant)  # isDenovo( GT ):
                # print GT
                if flag:
                    count -= 1
                    #nt("skipping isDenovo", familyVariant.familyInfo['fid'])
                    continue  # denovo

            # NOTE: main data set
            #dx.append( [fIx['newFid'], GT, cnt, qual] )
            dx.append(familyVariant)
            # notChild(index who is not child of any in this family)

        # NOTE: skip none found
        if len(dx) < 1:
            continue
        # skip if failed families are more than certain threshold
        # if len(dx)/(1.*len(fam))*100. < ox.minPercentOfGenotypeFamilies: continue

        nPC = 2 * count
        nPcntC = (1. * nPC) / (2 * len(fam)) * 100.
        for n, (p, v) in enumerate(izip(px, vx)):
            ix = n + 1
            # ref is index 0 and vx (variants) has only alternatives

            # some occasion '*' as one of alternatives
            if v.find('*') >= 0:
                continue

            strx = []
            cAlt, tAll = 0, 0
            # dx: fid, GT, cnt, notChild(index who is not child of any in this family)
            for familyVariant in dx:
                fid = familyVariant.familyInfo['newFid']
                GT = familyVariant.GT
                cnt = familyVariant.cnt
                nCi = familyVariant.familyInfo['notChild']
                # assume that all the ill-regualr genotype for X Y are correct
                # assume that all of auto have 2 copy, X non-Autosomal 1, and Y male(1) and female(0)

                tAll += sum(GT[nCi, :].sum(1))

                if sum(GT[:, ix]) < 1:
                    continue

                cAlt += sum(GT[nCi, ix])
                # only concern about non children

                strx.append(fid + ':' + array2str(GT, ix, delim='') +
                            ':' + familyVariant.get_cnt_str(ix))

            fC = len(strx)
            if fC < 1:
                continue

            strx = ';'.join(strx)
            # print strx

            tAll += 4 * count2

            # chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq
            # fid:bestState:counts:qualityScore
            # 11948:2112/0110:40 20 20 40/0 20 20 0:0:0;... writing format

            freqAlt = (1. * cAlt) / tAll * 100.

            #pix = 0
            #while (p,pix) in output: pix += 1

            if v.startswith('complex') or (p, v) in output:
                print >> sys.stdout, '\t'.join([chrom, str(p), v, strx, str(
                    nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)])
                continue

            if fC >= ox.tooManyThresholdFamilies:
                output[(p, v)] = (out, '\t'.join([chrom, str(p), v, 'TOOMANY', str(
                    nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]))
                output[(p, v + '*')] = (outTOOMANY,
                                        '\t'.join([chrom, str(p), v, strx]))
            else:
                output[(p, v)] = (out, '\t'.join([chrom, str(p), v, strx, str(
                    nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]))

    printSome(output)


if __name__ == "__main__":
    main()
