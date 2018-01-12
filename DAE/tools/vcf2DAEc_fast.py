#!/usr/bin/env python

from __future__ import division
import optparse
import sys
import os
from cyvcf2 import VCF
import numpy as np
from collections import namedtuple, defaultdict, OrderedDict
from itertools import izip, groupby, imap
import itertools
import variantFormat as vrtF
from ped2NucFam import *
import vrtIOutil as vIO
import heapq
import time
# add more data on fam Info


def merge(key, *iterables):
    h = []
    h_append = h.append

    _heapify = heapq.heapify
    _heappop = heapq.heappop
    _heapreplace = heapq.heapreplace

    for order, it in enumerate(map(iter, iterables)):
        try:
            next = it.next
            value = next()
            h_append([key(value), order, value, next])
        except StopIteration:
            pass
    _heapify(h)
    while len(h) > 1:
        try:
            while True:
                key_value, order, value, next = s = h[0]
                yield value
                value = next()
                s[0] = key(value)
                s[2] = value
                _heapreplace(h, s)
        except StopIteration:
            _heappop(h)
    if h:
        key_value, order, value, next = h[0]
        yield value
        for v in next.__self__:
            yield v


class Batch:
    def __init__(self, filename, fInfo, region):
        self.vf = VCF(filename)
        self.region = region
        self.samples_arr = np.asarray(self.vf.samples)
        individualToIndex = dict()
        for i, sampleId in enumerate(self.vf.samples):
            individualToIndex[sampleId] = i

        self.fam = famInVCF(fInfo, self.vf)

        self.individualToFamily = dict()

        for familyId in self.fam:
            familyInfo = fInfo[familyId]
            family = Family(familyInfo)

            indicies = []
            for personId in familyInfo['ids']:
                self.individualToFamily[personId] = family
            
            family.set_indicies(individualToIndex)

    def __iter__(self):
        def add_self(x):
            return {
                'batch': self,
                'variant': x
            }
        if self.region is not None:
            return imap(add_self, self.vf(self.region).__iter__())
        return imap(add_self, self.vf.__iter__())


class Family:
    def __init__(self, familyInfo):
        self.familyInfo = familyInfo

    def is_mendelian(self, arr):
        if ((arr[2] == arr[0] or arr[3] == arr[0]) and
                (arr[4] == arr[1] or arr[5] == arr[1])):
            return True
        if ((arr[2] == arr[1] or arr[3] == arr[1]) and
                (arr[4] == arr[0] or arr[5] == arr[0])):
            return True
        if arr[0] != arr[1]:
            if ((arr[2] == arr[0] and arr[3] == arr[1]) or
                    (arr[2] == arr[1] and arr[3] == arr[0])):
                if arr[4] != arr[5]:
                    return True
            if ((arr[4] == arr[0] and arr[5] == arr[1]) or
                    (arr[4] == arr[1] and arr[5] == arr[0])):
                if arr[2] != arr[3]:
                    return True
        return False

    def set_indicies(self, individualToIndex):
        indicies = []
        simple_indicies = []
        for personId in self.familyInfo['ids']:
            index = individualToIndex[personId] * 2
            indicies.append(index)
            indicies.append(index + 1)

            simple_indicies.append(individualToIndex[personId])

        self.indicies = np.array(indicies)
        self.simple_indicies = np.array(simple_indicies)

        self.families = []
        for iFM in self.familyInfo['iFM']:
            indicies = []
            for familyIndex in iFM:
                personId = self.familyInfo['ids'][familyIndex]
                index = individualToIndex[personId] * 2
                indicies.append(index)
                indicies.append(index + 1)
            self.families.append(indicies)

        parent_indicies = []
        for personId in self.familyInfo['notChild']:
            index = individualToIndex[self.familyInfo['ids'][personId]] * 2
            parent_indicies.append(index)
            parent_indicies.append(index + 1)

        self.parent_indicies = np.array(parent_indicies)

    def is_denovo(self, variant):
        for family in self.families:
            arr = variant[family]
            if not self.is_mendelian(arr):
                #print(self.familyInfo['newFid'])
                return True
        return False

    def variant_present(self, variant, index):
        data = variant.gt_idxs[self.indicies]
        return any(data == index)

    def variant_present_in_parent(self, variant, index):
        data = variant.gt_idxs[self.parent_indicies]
        return np.sum(data == index)

    def generate_gt(self, variant, index):
        refStr = []
        altStr = []
        addStr = []
        additional = False

        data = variant.gt_idxs[self.indicies]

        for i in range(0, len(data), 2):
            if data[i] == 0 and data[i + 1] == 0:
                refStr.append('2')
                altStr.append('0')
                addStr.append('0')
            elif data[i] == 0 or data[i + 1] == 0:
                if data[i] == index or data[i + 1] == index:
                    refStr.append('1')
                    altStr.append('1')
                    addStr.append('0')
                else:
                    refStr.append('1')
                    altStr.append('0')
                    addStr.append('1')
                    additional = True
            else:
                if data[i] == index and data[i + 1] == index:
                    refStr.append('0')
                    altStr.append('2')
                    addStr.append('0')
                elif data[i] == index or data[i + 1] == index:
                    refStr.append('0')
                    altStr.append('1')
                    addStr.append('1')
                    additional = True
                else:
                    refStr.append('0')
                    altStr.append('0')
                    addStr.append('2')
                    additional = True

        if additional:
            return "{}/{}/{}".format(''.join(refStr),
                                     ''.join(altStr),
                                     ''.join(addStr))
        else:
            return "{}/{}".format(''.join(refStr), ''.join(altStr))

    def generate_cnt(self, variant, index, altsCount):
        refCnt = ' '.join([str(i)
                          for i in
                          variant.gt_ref_depths[self.simple_indicies]])
        altCnt = ' '.join([str(variant.gt_alt_depths[i + index])
                          for i in self.simple_indicies * (altsCount + 1)])

        addCnt = []
        additional = False

        if altsCount > 1:
            for i in self.simple_indicies * (altsCount + 1):
                r = [c for c in range(i + 1, i + altsCount + 1)
                     if c != i + index]
                addSum = np.sum(variant.gt_alt_depths[r])
                addCnt.append(str(addSum))

                if addSum > 0:
                    additional = True
        
        if additional:
            addCnt = ' '.join(addCnt)
            return "{}/{}/{}".format(refCnt, altCnt, addCnt)
        return "{}/{}".format(refCnt, altCnt)


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
    start_time = time.time()
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
    
    parser.add_option("-r", "--region", dest="region", default=None,
                      metavar="region", help="parse only selected region")

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

    output_count = 0

    with open(OUT, 'w') as out, open(TOOMANY, 'w') as outTOOMANY:
        print >> out, '\t'.join(
            'chr,position,variant,familyData,all.nParCalled,all.prcntParCalled,all.nAltAlls,all.altFreq'.split(','))
        print >> outTOOMANY, '\t'.join(
            'chr,position,variant,familyData'.split(','))

        batches = [Batch(f, fInfo, ox.region) for f in dfile.split(",")]
        fam = [item for f in batches for item in f.fam]
        fam_count = len(fam)

        # # print family Info in a format
        FAMOUT = ox.outputPrefix + '-families.txt'
        printFamData(fInfo, pInfo, proj=ox.project, lab=ox.lab,
                     listFam=fam, out=open(FAMOUT, 'w'))

        def keyfunc(variant):
            return (variant['variant'].CHROM, variant['variant'].POS)
    
        for key, group in groupby(merge(keyfunc, *batches), keyfunc):
            chrom, pos = key

            allIterestingFamilies = set()
            allMissingFamilies = set()
            allFamilies = []
            variants = []
            missingCount = 0

            for variant in group:
                missingIndexes = np.where(variant['variant'].gt_types == 2)
                missingCount += missingIndexes[0].shape[0]
                missingIds = variant['batch'].samples_arr[missingIndexes]

                individualToFamily = variant['batch'].individualToFamily

                interestingIndexes = np.where(np.logical_or(
                    variant['variant'].gt_types == 1,
                    variant['variant'].gt_types == 3))

                interestingIds = variant['batch'].samples_arr[interestingIndexes]
                interestingFamilies = {individualToFamily[individual]
                                       for individual in interestingIds
                                       if individual in individualToFamily}
                allIterestingFamilies |= interestingFamilies

                missingFamilies = {individualToFamily[individual]
                                   for individual in missingIds
                                   if individual in individualToFamily}
                allMissingFamilies |= missingFamilies

                families = [family
                            for family in sorted(interestingFamilies - missingFamilies,
                                                 key=lambda(x): x.familyInfo['newFid'])
                            if not family.is_denovo(variant['variant'].gt_idxs)]
                allFamilies.extend(families)

                px, vx = vrtF.vcf2cshlFormat2(variant['variant'].POS,
                                              variant['variant'].REF,
                                              variant['variant'].ALT)

                for n, (p, v) in enumerate(izip(px, vx)):
                    variants.append((n, p, v, variant, families))

            pgt = (1 - missingCount / (4 * fam_count)) * 100
            if pgt < ox.minPercentOfGenotypeSamples:
                continue

            for key, group in groupby(sorted(variants, key=lambda x: (x[1], x[2])), lambda x: (x[1], x[2])):
                p, v = key

                if v.find('*') >= 0:
                        continue
                output = []

                cnt_in_parent = 0

                for g in group:
                    n, p, v, variant, families = g
                    altsCount = len(variant['variant'].ALT)
                    for family in families:
                        familyInfo = family.familyInfo

                        if not family.variant_present(variant['variant'], n + 1):
                            continue

                        GT = family.generate_gt(variant['variant'], n + 1)
                        cnt = family.generate_cnt(variant['variant'], n + 1, altsCount)

                        cnt_in_parent += family.variant_present_in_parent(
                            variant['variant'], n + 1)
                        output.append((familyInfo['newFid'], GT, cnt))
                if len(output) < 1:
                    continue
                
                l = len(output)
                strx = ["{}:{}:{}".format(familyId, GT, cnt)
                        for familyId, GT, cnt in sorted(output, key=lambda x: x[0])]
                strx = ';'.join(strx)
                
                # print strx
                dnv_count = len(allIterestingFamilies - allMissingFamilies) - len(allFamilies)
                count = fam_count - len(allMissingFamilies)

                tAll = 4 * len(allFamilies)
                tAll += 4 * (fam_count - len(allMissingFamilies) - len(allIterestingFamilies - allMissingFamilies))
                nPC = (count - dnv_count) * 2

                nPcntC = (count - dnv_count) / fam_count * 100
                cAlt = cnt_in_parent
                freqAlt = (1. * cAlt) / tAll * 100.

                output_count += 1

                if v.startswith('complex'):
                    print >> sys.stdout, '\t'.join([chrom, str(p), v, strx, str(
                        nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)])
                    continue

                if l >= ox.tooManyThresholdFamilies:
                    print >> out, '\t'.join([chrom, str(p), v, 'TOOMANY', str(
                        nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)])
                    print >> outTOOMANY, '\t'.join([chrom, str(p), v, strx])
                else:
                    print >> out, '\t'.join([chrom, str(p), v, strx, str(
                        nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)])
                
                if output_count % 1000 == 0:
                    sys.stdout.write("\r%d records ok time: %d secs" % (output_count, time.time() - start_time))
                    sys.stdout.flush()
    
    sys.stdout.write("\rDone: %d records ok time: %d secs\n" % (output_count, time.time() - start_time))
    sys.stdout.flush()

if __name__ == "__main__":
    main()

