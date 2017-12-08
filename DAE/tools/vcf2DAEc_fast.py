#!/usr/bin/env python

from __future__ import division
import optparse
import sys
import os
from cyvcf2 import VCF
import numpy as np
from collections import namedtuple, defaultdict, OrderedDict
from itertools import izip
import itertools

#from vcf2DAEutil import *
import variantFormat as vrtF
from ped2NucFam import *
import vrtIOutil as vIO


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


def isDenovo(st, fm):  # fm : fa and ma index
    mdl = mStat[(2, 2, 2)]

    for c, f, m in fm:  # fa ma child index
        for n, s in enumerate(st[c, :]):
            if s not in mdl[(st[f, n], st[m, n])]:
                # print st
                return True
            # print f,m,c,n,s, (st[f,n],st[m,n])

    return False


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


def famInVCF(fInfo, vcf):
    fam = []
    for fid in sorted(fInfo.keys()):
        flag = False

        mm = []
        for sm in fInfo[fid]['ids']:
            if sm in vcf.samples:
                continue

            flag = True
            mm.append(sm)

        if flag:
            #print >> sys.stderr, '\t'.join(
            #    ['family',  fid, 'notComplete', 'missing', ','.join(mm)])
            continue

        fam.append(fid)

    return fam


def digitP(x): 
    return '{:.4f}'.format(x)


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
    vf = VCF(dfile)
    fam = famInVCF(fInfo, vf)
    fam_count = len(fam)

    # print family Info in a format
    FAMOUT = ox.outputPrefix + '-families.txt'
    printFamData(fInfo, pInfo, proj=ox.project, lab=ox.lab,
                 listFam=fam, out=open(FAMOUT, 'w'))

    individualToFamily = dict()
    individualToIndex = dict()

    samples_arr = np.asarray(vf.samples)
    for i, sampleId in enumerate(vf.samples):
        individualToIndex[sampleId] = i

    for familyId in fam:
        familyInfo = fInfo[familyId]

        indicies = []
        for personId in familyInfo['ids']:
            individualToFamily[personId] = familyId
            index = individualToIndex[personId] * 2
            indicies.append(index)
            indicies.append(index + 1)

        familyInfo['indicies'] = np.array(indicies)

    output = {}
    for variant in vf:
        missingIndexes = np.where(variant.gt_types == 2)
        missingIds = samples_arr[missingIndexes]

        pgt = (1 - missingIndexes[0].shape[0] / len(samples_arr)) * 100
        if pgt < ox.minPercentOfGenotypeSamples:
            continue

        chrom = variant.CHROM
        px, vx = vrtF.vcf2cshlFormat2(variant.POS, variant.REF, variant.ALT)

        families = []

        altsCount = len(variant.ALT)
        interestingIndexes = np.where(np.logical_or(variant.gt_types == 1,
                                                    variant.gt_types == 3))
        interestingIds = samples_arr[interestingIndexes]
        interestingFamilies = {individualToFamily[individual]
                               for individual in interestingIds
                               if individual in individualToFamily}

        missingFamilies = {individualToFamily[individual]
                           for individual in missingIds
                           if individual in individualToFamily}

        dx = []

        count = fam_count - len(missingFamilies)
        #print(interestingFamilies)
        #print(missingFamilies)

        for familyId in sorted(interestingFamilies - missingFamilies):
            familyInfo = fInfo[familyId]
            fam = familyInfo['ids']
            GT = np.zeros((len(fam), altsCount + 1,), dtype=numpy.int)
            cnt = np.zeros((len(fam), altsCount + 1,), dtype=numpy.int)
            for i, personId in enumerate(fam):
                index = individualToIndex[personId]
                gt_type = variant.gt_types[index]

                #print(fam, personId, variant.gt_types[index])

                p = 1
                if gt_type == 0:
                    GT[i][0] = 2
                else:
                    p = variant.gt_idxs[index * 2]
                    GT[i][p] += 1
                    p = variant.gt_idxs[index * 2 + 1]
                    GT[i][p] += 1
          
                cnt[i][0] = variant.gt_ref_depths[index]

                for k in range(1, altsCount + 1):
                    cnt[i][k] = variant.gt_alt_depths[index * (altsCount + 1) + k]

            flag = isDenovo(GT, familyInfo['iFM'])  # isDenovo( GT ):
            if flag:
                count -= 1
                continue  # denovo

            # NOTE: main data set
            #dx.append( [fIx['newFid'], GT, cnt, qual] )
            dx.append([familyInfo['newFid'], GT, cnt, familyInfo['notChild']])

        if len(dx) < 1:
            continue
        # skip if failed families are more than certain threshold
        # if len(dx)/(1.*len(fam))*100. < ox.minPercentOfGenotypeFamilies: continue
        #print("bef", count)

        #print(len(interestingFamilies), len(missingFamilies), len(dx), count)

        nPC = 2 * count
        nPcntC = (1. * nPC) / (2 * fam_count) * 100.
        for n, (p, v) in enumerate(izip(px, vx)):
            ix = n + 1
            # ref is index 0 and vx (variants) has only alternatives

            # some occasion '*' as one of alternatives
            if v.find('*') >= 0:
                continue

            strx = []
            cAlt = 0
            tAll = 4 * len(dx)
            # dx: fid, GT, cnt, notChild(index who is not child of any in this family)
            for (fid, GT, cnt, nCi) in dx:
                # assume that all the ill-regualr genotype for X Y are correct
                # assume that all of auto have 2 copy, X non-Autosomal 1, and Y male(1) and female(0)
                #tAll += sum(GT[nCi, :].sum(1))
                #print(GT)
                #print(nCi)
                #print(GT[nCi, :])
                #print(sum(GT[nCi, :].sum(1)))
                if sum(GT[:, ix]) < 1:
                    continue              

                cAlt += sum(GT[nCi, ix])
                # only concern about non children

                strx.append(fid + ':' + array2str(GT, ix, delim='') +
                            ':' + array2str(cnt, ix, delim=' '))

            fC = len(strx)
            if fC < 1:
                continue

            strx = ';'.join(strx)
            # print strx

            tAll += 4 * (fam_count - len(missingFamilies) - len(interestingFamilies - missingFamilies))

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
