#!/bin/env python

from DAE import *
from GeneTerms import loadGeneTerm
from scipy import stats
import sys

class EnrichmentTestRes:
    pass

def enrichmentTest(testVarGenesDict, geneTerms):
    allRes = {}

    for s in geneTerms.t2G:
        allRes[s] = {}
     
    for tName in testVarGenesDict:
        for s in geneTerms.t2G:
            allRes[s][tName] = EnrichmentTestRes();
            allRes[s][tName].cnt = 0
        for v in testVarGenesDict[tName]:
            vSets = set()
            for gs in [ x['sym'] for x in v.requestedGeneEffects ]:
                if gs in geneTerms.g2T:
                    vSets|=set(geneTerms.g2T[gs])
            for s in vSets:
                allRes[s][tName].cnt +=1

    totals = {}
    for tName in testVarGenesDict:
        totals[tName] = len(testVarGenesDict[tName])
    
    bcgTotal = totals['BACKGROUND']
    for s in geneTerms.t2G:
        bcgInSet = allRes[s]['BACKGROUND'].cnt
        if bcgInSet == 0:
            bcgInSet = 0.5
        backProb = float(bcgInSet)/bcgTotal

        for tName in testVarGenesDict:
            res = allRes[s][tName]    
            total = totals[tName]

            res.pVal = p = stats.binom_test(res.cnt, total, p=backProb)
            res.expected = round(backProb*total, 4)

    for tName in testVarGenesDict:
        sp = [ (s, trs[tName].pVal) for s,trs in allRes.items() ]
        qVals = computeQVals([x[1] for x in sp])
        for a,qVal in zip(sp,qVals):
            allRes[a[0]][tName].qVal = qVal

    return allRes, totals
                                
def computeQVals(pVals):
    ss = sorted([(i,p) for i,p in enumerate(pVals)], key=lambda x: x[1])
    qVals = [ip[1]*len(ss)/(j+1) for j,ip in enumerate(ss)];
    prevPVal = ss[-1][1]
    prevQVal = qVals[-1]
    for i in xrange(len(ss)-2,-1,-1):
        if ss[i][1] == prevPVal:
            qVals[i] = prevQVal
        else:
            prevPVal = ss[i][1]
            prevQVal = qVals[i]
    return [ q  for d,q in sorted(zip(ss,qVals), key=lambda x: x[0][0])]

def printSummaryTable(geneTerms,allRes,totals,tTests=None):
    if tTests==None:
        tTests = sorted([x for x in totals.keys() if x != "BACKGROUND"])
    print "\t\t\t\t\t" + "\t\t\t\t\t".join(tTests)
    bcgTotal = totals['BACKGROUND'];
    hcols = []
    hcols.extend(("setId", "setDesc", "NumberOfGenes", "BackgroundOverlap (" + str(bcgTotal) + ")", "BackgroundProportion"));
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
                pVal= str('%.1E'% (res.pVal))

            if res.qVal >= 0.0001:
                qVal = str(round(res.qVal, 4))
            else:
                qVal= str('%.1E'% (res.qVal))

            expected = str(round(res.expected, 4))

            if res.cnt > res.expected:
                lessmore = "more"
            elif res.cnt < res.expected:
                lessmore = "less"
            else:
                lessmore = "equal"
            cols.extend((str(res.cnt), expected, pVal, qVal, lessmore))
        print "\t".join(cols)


if __name__ == "__main__":
    # setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/miRNA-TargetScan6.0-Conserved'
    setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/GeneSets'

    if len(sys.argv)>1:
        setsFile=sys.argv[1]

    geneTerms = loadGeneTerm(setsFile)


    wigStudy = vDB.get_study('wig683')
    wigStds= [wigStudy]
    allStds= [wigStudy, 
                vDB.get_study('StateWE2012'), 
                vDB.get_study('EichlerWE2012'), 
                vDB.get_study('DalyWE2012'),
                vDB.get_study('wigState333'),
                vDB.get_study('wigEichler374')]

    testVarGenesDict = {}
    testVarGenesDict['LGDs_Auts_allStudies'] =      list(vDB.get_denovo_variants(allStds,inChild='prb',  effectTypes="LGDs"))
    testVarGenesDict['LGDs_Auts_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='prb',  effectTypes="LGDs"))
    testVarGenesDict['LGDs_AutM_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='prbM', effectTypes="LGDs"))
    testVarGenesDict['LGDs_AutF_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='prbF', effectTypes="LGDs"))
    testVarGenesDict['LGDs_Sibs_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='sib',  effectTypes="LGDs"))
    testVarGenesDict['LGDs_SibM_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='sibM', effectTypes="LGDs"))
    testVarGenesDict['LGDs_SibF_wiglerOnly'] =    list(vDB.get_denovo_variants(wigStds,inChild='sibF', effectTypes="LGDs"))
    testVarGenesDict['missense_Auts'] =           list(vDB.get_denovo_variants(wigStds,inChild='prb',  effectTypes="missense"))
    testVarGenesDict['missense_Sibs'] =           list(vDB.get_denovo_variants(wigStds,inChild='sib',  effectTypes="missense"))
    testVarGenesDict['synonymous_Auts'] =         list(vDB.get_denovo_variants(wigStds,inChild='prb',  effectTypes="synonymous"))
    testVarGenesDict['synonymous_Sibs'] =         list(vDB.get_denovo_variants(wigStds,inChild='sib',  effectTypes="synonymous"))

    testVarGenesDict['ultrarareKillersParents'] = list(wigStudy.get_transmitted_summary_variants(ultraRareOnly=True, effectTypes="LGDs"))
    testVarGenesDict['BACKGROUND'] =              list(wigStudy.get_transmitted_summary_variants(ultraRareOnly=True, effectTypes="synonymous"))

    print >> sys.stderr, "Running the test..."
    allRes, totals = enrichmentTest(testVarGenesDict, geneTerms)
    print >> sys.stderr, "Preparing the summary table..."
    printSummaryTable(geneTerms,allRes,totals,
        ['LGDs_Auts_allStudies', 'LGDs_Auts_wiglerOnly', 'LGDs_AutM_wiglerOnly', 'LGDs_AutF_wiglerOnly', 
        'LGDs_Sibs_wiglerOnly', 'LGDs_SibM_wiglerOnly', 'LGDs_SibF_wiglerOnly', 
        'missense_Auts', 'missense_Sibs', 
        'synonymous_Auts', 'synonymous_Sibs', 
        'ultrarareKillersParents'])
    print >> sys.stderr, "Done!"
    
