#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from builtins import map, zip

import argparse
import sys
import os
from cyvcf2 import VCF
import numpy as np
from itertools import groupby

from ped2NucFam import procFamInfo, printFamData
# import heapq
import time
import re
import toolz

from utils.vcf_utils import cshl_format, trim_str_back
from DAE import genomesDB as genomes_db

# add more data on fam Info


# def merge(key, *iterables):
#     h = []
#     h_append = h.append

#     _heapify = heapq.heapify
#     _heappop = heapq.heappop
#     _heapreplace = heapq.heapreplace

#     for order, it in enumerate(map(iter, iterables)):
#         try:
#             next = it.next
#             value = next()
#             h_append([key(value), order, value, next])
#         except StopIteration:
#             pass
#     _heapify(h)
#     while len(h) > 1:
#         try:
#             while True:
#                 key_value, order, value, next = s = h[0]
#                 yield value
#                 value = next()
#                 s[0] = key(value)
#                 s[2] = value
#                 _heapreplace(h, s)
#         except StopIteration:
#             _heappop(h)
#     if h:
#         key_value, order, value, next = h[0]
#         yield value
#         for v in next.__self__:
#             yield v


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

            # indicies = []
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
            return map(add_self, self.vf(self.region).__iter__())
        return map(add_self, self.vf.__iter__())


class Family:
    def __init__(self, familyInfo):
        self.familyInfo = familyInfo
        self.pars_x_check = genomes_db.get_pars_x_test()
        self.pars_y_check = genomes_db.get_pars_y_test()

    def is_mendelian(self, arr):
        if ((arr[2] == arr[0] or arr[3] == arr[0]) and
                (arr[4] == arr[1] or arr[5] == arr[1])):
            return True
        if ((arr[2] == arr[1] or arr[3] == arr[1]) and
                (arr[4] == arr[0] or arr[5] == arr[0])):
            return True
        return False

    def is_mendelian_male_X(self, arr):
        if arr[0] != arr[1]:
            return False

        if (arr[4] == arr[0] or arr[5] == arr[0]):
            return True
        return False

    def is_mendelian_male_Y(self, arr):
        if arr[0] != arr[1]:
            return False

        if (arr[2] == arr[0] or arr[3] == arr[0]):
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
            isChildMale = self.familyInfo['isMale'][iFM[0]] == 1
            self.families.append((isChildMale, indicies))

        parent_indicies = []
        for personId in self.familyInfo['notChild']:
            index = individualToIndex[self.familyInfo['ids'][personId]] * 2
            parent_indicies.append(index)
            parent_indicies.append(index + 1)

        self.parent_indicies = np.array(parent_indicies)

    def is_autosomal_region(self, chrom, variant):
        if chrom.endswith('X'):
            return self.pars_x_check(chrom, variant.POS)
        if chrom.endswith('Y'):
            return self.pars_y_check(chrom, variant.POS)
        return True
        # if variant.CHROM == 'chrX':
        #     if variant.start >= 10000 and variant.end <= 2781479:
        #         return True
        #     if variant.start >= 155701382 and variant.end <= 156030895:
        #         return True
        #     return False
        # if variant.CHROM == 'chrY':
        #     if variant.start >= 10000 and variant.end <= 2781479:
        #         return True
        #     if variant.start >= 56887902 and variant.end <= 57217415:
        #         return True
        #     return False
        # return True

    def is_denovo(self, chrom, variant):
        for isChildMale, family in self.families:
            arr = variant.gt_idxs[family]

            if isChildMale:
                if self.is_autosomal_region(chrom, variant):
                    if not self.is_mendelian(arr):
                        return True
                elif chrom.endswith('X') and \
                        not self.is_mendelian_male_X(arr):
                    return True
                elif chrom.endswith('Y') and \
                        not self.is_mendelian_male_Y(arr):
                    return True
            else:
                if chrom.endswith('Y') and \
                        not self.is_mendelian(arr):
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
        sx = np.zeros((lx,), dtype=np.int)
        for n, mx in enumerate(v['newIds']):
            s = pInfo[mx].sex
            if s == '1':
                sx[n] = 1
        v['isMale'] = sx

        cl = len(v['famaIndex'])
        idxMF = np.zeros((cl, 3,), dtype=np.int)
        nC = list(range(lx))
        for n, (a, b) in enumerate(v['famaIndex'].items()):
            idxMF[n, :] = [a, b.fa, b.ma]
            nC.remove(a)
        v['iFM'] = idxMF
        v['notChild'] = np.array(nC)

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
            # print >> sys.stderr, '\t'.join(
            #    ['family',  fid, 'notComplete', 'missing', ','.join(mm)])
            continue

        fam.append(fid)

    return fam


def digitP(x):
    return '{:.4f}'.format(x)


def vcf2cshlFormat2(pos, ref, alts):
    vrt, pxx = list(), list()
    for alt in alts:
        p, v, _ = cshl_format(pos, ref, alt, trimmer=trim_str_back)

        pxx.append(p)
        vrt.append(v)

    return pxx, vrt


def main():

    start_time = time.time()
    # svip.ped
    # svip-FB-vars.vcf.gz, svip-PL-vars.vcf.gz, svip-JHC-vars.vcf.gz
    # pfile, dfile = 'data/svip.ped', 'data/svip-FB-vars.vcf.gz'

    parser = argparse.ArgumentParser(
        description="converts list of VCF files to DAE transmitted varaints")

    parser.add_argument(
        'pedigree', type=str,
        metavar='<pedigree filename>',
        help='families file in pedigree format'
    )
    parser.add_argument(
        'vcf', type=str,
        metavar='<VCF filename>',
        help='VCF file to import'
    )

    parser.add_argument(
        "-x", "--project", dest="project", default="VIP",
        metavar="project", help="project name")
    parser.add_argument(
        "-l", "--lab", dest="lab", default="SF",
        metavar="lab", help="lab name")

    parser.add_argument(
        "-o", "--outputPrefix", dest="outputPrefix", default="transmission",
        metavar="outputPrefix", help="prefix of output transmission file")

    parser.add_argument(
        "-m", "--minPercentOfGenotypeSamples",
        dest="minPercentOfGenotypeSamples", type=float, default=25.,
        metavar="minPercentOfGenotypeSamples",
        help="threshold percentage of gentyped samples to printout "
        "[default: 25]")
    parser.add_argument(
        "-t", "--tooManyThresholdFamilies", dest="tooManyThresholdFamilies",
        type=int, default=10,
        metavar="tooManyThresholdFamilies", 
        help="threshold for TOOMANY to printout [defaylt: 10]")

    parser.add_argument(
        "-s", "--missingInfoAsNone", action="store_true", 
        dest="missingInfoAsNone", default=False,
        help="missing sample Genotype will be filled with 'None' for many "
        "VCF files input")

    parser.add_argument(
        "--chr", action="store_true", 
        dest="prepend_chr", default=False,
        help="adds prefix to 'chr' to contig names")

    parser.add_argument(
        "--nochr", action="store_true", 
        dest="remove_chr", default=False,
        help="removes prefix to 'chr' from contig names")

    parser.add_argument(
        "-r", "--region", dest="region", default=None,
        metavar="region", help="parse only selected region")

    args = parser.parse_args()
    pfile = args.pedigree
    dfile = args.vcf

    # missingInfoAsRef = True
    # if ox.missingInfoAsNone:
    #     missingInfoAsRef = False  # ; print NNN

    # print famFile
    # fInfo: each fam has mom, dad and child personal ID, old and new Ids
    # pInfo: each person has raw info from "PED" file
    fInfo, pInfo = procFamInfo(pfile)
    # add more info to fInfo such as
    #    notChild: who is not children
    #    iFM     : fa and ma index for each child in families
    #    isMale  : sex info in the order of ids and newIds
    #               (they have the same order)
    makeFamInfoConv(fInfo, pInfo)

    if os.path.isfile(args.outputPrefix + '.txt'):
        print(
            args.outputPrefix + '.txt: already exist',
            file=sys.stderr)
        exit(1)

    # setup to print transmission files
    OUT = args.outputPrefix + '.txt'
    TOOMANY = args.outputPrefix + '-TOOMANY.txt'

    output_count = 0
    start_region = None
    if args.region is not None:
        start_region = int(re.match(
            "chr([0-9X]+):([0-9]+)-([0-9]+)", args.region).group(2))

    with open(OUT, 'w') as out, open(TOOMANY, 'w') as outTOOMANY:
        print(
            '\t'.join(
                'chr,position,variant,familyData,all.nParCalled,'
                'all.prcntParCalled,all.nAltAlls,all.altFreq'.split(',')),
            file=out)
        print(
            '\t'.join(
                'chr,position,variant,familyData'.split(',')),
            file=outTOOMANY)

        batches = [Batch(f, fInfo, args.region) for f in dfile.split(",")]
        fam = [item for f in batches for item in f.fam]
        fam_count = len(fam)

        # # print family Info in a format
        FAMOUT = args.outputPrefix + '-families.txt'

        # FIXME: Do not reduce families because some people are not sequenced
        # printFamData(fInfo, pInfo, proj=ox.project, lab=ox.lab,
        #              listFam=fam, out=open(FAMOUT, 'w'))
        printFamData(fInfo, pInfo, proj=args.project, lab=args.lab,
                     listFam=[], out=open(FAMOUT, 'w'))

        def keyfunc(variant):
            return (variant['variant'].CHROM, variant['variant'].POS)

        if len(batches) == 1:
            batch_stream = batches[0]
        else:
            batch_stream = toolz.merge_sorted(batches, keyfunc)

        if args.prepend_chr:
            assert not args.remove_chr

            def contig_fixer(chrom):
                return "chr{}".format(chrom)
        elif args.remove_chr:

            def contig_fixer(chrom):
                if chrom.startswith("chr"):
                    return chrom[3:]
                else:
                    return chrom

        else:
            def contig_fixer(chrom):
                return chrom

        for key, group in groupby(batch_stream, keyfunc):
            chrom, pos = key
            chrom = contig_fixer(chrom)

            if start_region is not None and start_region > pos:
                continue

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

                interestingIds = variant['batch'].\
                    samples_arr[interestingIndexes]
                interestingFamilies = {individualToFamily[individual]
                                       for individual in interestingIds
                                       if individual in individualToFamily}
                allIterestingFamilies |= interestingFamilies

                missingFamilies = {individualToFamily[individual]
                                   for individual in missingIds
                                   if individual in individualToFamily}
                allMissingFamilies |= missingFamilies

                families = [
                    family
                    for family in sorted(
                        interestingFamilies - missingFamilies,
                        key=lambda x: x.familyInfo['newFid'])
                    if not family.is_denovo(chrom, variant['variant'])]
                allFamilies.extend(families)

                px, vx = vcf2cshlFormat2(
                    variant['variant'].POS,
                    variant['variant'].REF,
                    variant['variant'].ALT)

                for n, (p, v) in enumerate(zip(px, vx)):
                    variants.append((n, p, v, variant, families))

            pgt = (1 - missingCount / (4 * fam_count)) * 100
            if pgt < args.minPercentOfGenotypeSamples:
                continue

            for key, group in groupby(
                    sorted(
                        variants,
                        key=lambda x: (x[1], x[2])), lambda x: (x[1], x[2])):
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

                        if not family.variant_present(
                                variant['variant'], n + 1):
                            continue

                        GT = family.generate_gt(
                            variant['variant'], n + 1)
                        cnt = family.generate_cnt(
                            variant['variant'], n + 1, altsCount)

                        cnt_in_parent += family.variant_present_in_parent(
                            variant['variant'], n + 1)
                        output.append((familyInfo['newFid'], GT, cnt))
                if len(output) < 1:
                    continue

                ll = len(output)
                strx = [
                    "{}:{}:{}".format(familyId, gt, count)
                    for familyId, gt, count in sorted(
                        output, key=lambda x: x[0])
                ]
                strx = ';'.join(strx)

                # print strx
                dnv_count = len(allIterestingFamilies - allMissingFamilies) - \
                    len(allFamilies)
                count = fam_count - len(allMissingFamilies)

                tAll = 4 * len(allFamilies)
                tAll += 4 * (
                    fam_count - len(allMissingFamilies) -
                    len(allIterestingFamilies - allMissingFamilies))
                nPC = (count - dnv_count) * 2

                nPcntC = (count - dnv_count) / fam_count * 100
                cAlt = cnt_in_parent
                freqAlt = (1. * cAlt) / tAll * 100.

                output_count += 1

                if v.startswith('complex'):
                    print(
                        '\t'.join([chrom, str(p), v, strx, str(
                            nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]),
                        file=out)
                    continue

                if ll >= args.tooManyThresholdFamilies:
                    print(
                        '\t'.join([chrom, str(p), v, 'TOOMANY', str(
                            nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]),
                        file=out)
                    print(
                        '\t'.join([chrom, str(p), v, strx]),
                        file=outTOOMANY)
                else:
                    print(
                        '\t'.join([chrom, str(p), v, strx, str(
                            nPC), digitP(nPcntC), str(cAlt), digitP(freqAlt)]),
                        file=out)

                if output_count % 1000 == 0:
                    sys.stdout.write(
                        "\n%d records ok time: %d secs" % 
                        (output_count, time.time() - start_time))
                    sys.stdout.flush()

    sys.stdout.write(
        "\nDone: %d records ok time: %d secs\n" %
        (output_count, time.time() - start_time))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
