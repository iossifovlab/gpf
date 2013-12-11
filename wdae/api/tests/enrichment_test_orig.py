#!/bin/env python

from DAE import *
from GeneTerms import *
from scipy import stats
import sys
from itertools import groupby
from collections import Counter

class EnrichmentTestRes:
    pass

def enrichmentTest(testVarGenesDict, geneTerms):
    allRes = {}

    for s in geneTerms.t2G:
        allRes[s] = {}

    for tName, gSyms in testVarGenesDict:
        for s in geneTerms.t2G:
            allRes[s][tName] = EnrichmentTestRes();
            allRes[s][tName].cnt = 0
        for gsg in gSyms:
            touchedSets = set()
            for gs in gsg:
                touchedSets |= set(geneTerms.g2T[gs])
            for s in touchedSets:
                allRes[s][tName].cnt += 1

    totals = {tName: len(gSyms) for tName, gSyms in testVarGenesDict}

    bcgTotal = totals['BACKGROUND']
    for s in geneTerms.t2G:
        bcgInSet = allRes[s]['BACKGROUND'].cnt
        if bcgInSet == 0:
            bcgInSet = 0.5
        backProb = float(bcgInSet)/bcgTotal

        for tName, gSyms in testVarGenesDict:
            res = allRes[s][tName]
            total = totals[tName]

            res.pVal = p = stats.binom_test(res.cnt, total, p=backProb)
            res.expected = round(backProb*total, 4)

    for tName, gSyms in testVarGenesDict:
        sp = [(s, trs[tName].pVal) for s, trs in allRes.items()]
        qVals = computeQVals([x[1] for x in sp])
        for a, qVal in zip(sp, qVals):
            allRes[a[0]][tName].qVal = qVal

    return allRes, totals


def computeQVals(pVals):
    ss = sorted([(i, p) for i, p in enumerate(pVals)], key=lambda x: x[1])
    qVals = [ip[1]*len(ss)/(j+1) for j,ip in enumerate(ss)]
    qVals = [q if q <= 1.0 else 1.0 for q in qVals]
    prevQVal = qVals[-1]
    for i in xrange(len(ss)-2, -1, -1):
        if qVals[i] > prevQVal:
            qVals[i] = prevQVal
        else:
            prevQVal = qVals[i]
    return [q  for d, q in sorted(zip(ss,qVals), key=lambda x: x[0][0])]


def printSummaryTable(testVarGenesDict, geneTerms, allRes, totals):
    tTests = [tn for tn, vs in testVarGenesDict if tn != "BACKGROUND"]
    print "\t\t\tBACKGROUND (UR syn.)\t\t" + "\t\t\t\t\t".join(tTests)
    bcgTotal = totals['BACKGROUND'];
    hcols = []
    hcols.extend(("setId", "setDesc", "GeneNumber", "Overlap (" + str(bcgTotal) + ")", "proportion"));
    for tTname in tTests:
        hcols.extend(("Overlap (" + str(totals[tTname]) + ")", "Expected", "pVal", "qVal", "lessOrMore"));
    print "\t".join(hcols)
    for s in geneTerms.t2G:
        cols = []
        bcgCnt = allRes[s]['BACKGROUND'].cnt
        bcgProp = str(round(float(bcgCnt)/bcgTotal,3));
        cols.extend((s,geneTerms.tDesc[s],str(len(geneTerms.t2G[s])), str(bcgCnt), bcgProp))
        for tTname in tTests:
            res = allRes[s][tTname]

            if res.pVal >= 0.0001:
                pVal = str(round(res.pVal, 4))
            else:
                pVal = str('%.1E' % (res.pVal))

            if res.qVal >= 0.0001:
                qVal = str(round(res.qVal, 4))
            else:
                qVal = str('%.1E' % (res.qVal))

            expected = str(round(res.expected, 4))

            if res.cnt > res.expected:
                lessmore = "more"
            elif res.cnt < res.expected:
                lessmore = "less"
            else:
                lessmore = "equal"
            cols.extend((str(res.cnt), expected, pVal, qVal, lessmore))
        print "\t".join(cols)


def fltDnv(vs):
    seen = set()
    ret = []
    for v in vs:
        vGss = [gs for gs in set([ge['sym'] for ge in v.requestedGeneEffects]) if (v.familyId + gs) not in seen]
        if not vGss:
            continue
        for gs in vGss:
            seen.add(v.familyId + gs)
        ret.append(vGss)
    return ret


def fltInh(vs):
    return [set([ge['sym'] for ge in v.requestedGeneEffects]) for v in vs]


def oneVariantPerRecurrent(vs):
    gnSorted = sorted([[ge['sym'], v] for v in vs
                       for ge in v.requestedGeneEffects])
    sym2Vars = {sym: [t[1] for t in tpi]
                for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
    sym2FN = {sym: len(set([v.familyId for v in vs]))
              for sym, vs in sym2Vars.items()}
    return [[gs] for gs, fn in sym2FN.items() if fn > 1]


def main(dnvSts, transmStdy, geneTerms):
    testVarGenesDict = [
        ['De novo recPrbLGDs',
         oneVariantPerRecurrent(
             vDB.get_denovo_variants(dnvSts,
                                     inChild='prb',
                                     effectTypes="LGDs"))],
        ['De novo prbLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prb',
                                        effectTypes="LGDs"))],
        ['De novo prbMaleLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prbM',
                                        effectTypes="LGDs"))],
        ['De novo prbFemaleLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prbF',
                                        effectTypes="LGDs"))],
        ['De novo sibLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='sib',
                                        effectTypes="LGDs"))],
        ['De novo sibMaleLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='sibM',
                                        effectTypes="LGDs"))],
        ['De novo sibFemaleLGDs',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='sibF',
                                        effectTypes="LGDs"))],
        ['De novo prbMissense',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prb',
                                        effectTypes="missense"))],
        ['De novo prbMaleMissense',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prbM',
                                        effectTypes="missense"))],
        ['De novo prbFemaleMissense',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prbF',
                                        effectTypes="missense"))],
        ['De novo sibMissense',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='sib',
                                        effectTypes="missense"))],
        ['De novo prbSynonymous',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='prb',
                                        effectTypes="synonymous"))],
        ['De novo sibSynonymous',
         fltDnv(vDB.get_denovo_variants(dnvSts,
                                        inChild='sib',
                                        effectTypes="synonymous"))],

        # ['UR LGDs in parents',
        #  fltInh(
        #      transmStdy.get_transmitted_summary_variants(
        #          ultraRareOnly=True,
        #          effectTypes="LGDs"))],
        ['BACKGROUND',
         fltInh(
             transmStdy.get_transmitted_summary_variants(
                 ultraRareOnly=True,
                 effectTypes="synonymous"))]
    ]

    print >> sys.stderr, "Running the test..."
    allRes, totals = enrichmentTest(testVarGenesDict, geneTerms)
    return testVarGenesDict, allRes, totals

if __name__ == "__main__":
    # setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/miRNA-TargetScan6.0-Conserved'
    # setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/GeneSets'

    setsFile = "main"
    denovoStudies = "allWE"
    transmittedStudy = "wig781"

    if len(sys.argv) > 1:
        setsFile = sys.argv[1]

    if len(sys.argv) > 2:
        denovoStudies = sys.argv[2]

    if len(sys.argv) > 3:
        transmittedStudy = sys.argv[3]

    if setsFile == 'denovo':
        geneTerms = vDB.get_denovo_sets(denovoStudies)
    else:
        try:
            geneTerms = giDB.getGeneTerms(setsFile)
        except:
            geneTerms = loadGeneTerm(setsFile)
            if geneTerms.geneNS=='id':
                def rF(x):
                    if x in giDB.genes:
                        return giDB.genes[x].sym
                geneTerms.renameGenes("sym", rF)
            if geneTerms.geneNS!='sym':
                raise Excpetion('Only work with id or sym namespace')

    transmStdy = vDB.get_study(transmittedStudy)
    dnvSts = vDB.get_studies(denovoStudies)

    testVarGenesDict, allRes, total = main(dnvSts, transmStdy, geneTerms)
    print >> sys.stderr, "Preparing the summary table..."
    printSummaryTable(testVarGenesDict, geneTerms, allRes, totals)

    print >> sys.stderr, "Done!"
