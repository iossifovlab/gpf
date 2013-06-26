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
     
    for tName,vs in testVarGenesDict:
        for s in geneTerms.t2G:
            allRes[s][tName] = EnrichmentTestRes();
            allRes[s][tName].cnt = 0
        for v in vs:
            vSets = set()
            for gs in [ x['sym'] for x in v.requestedGeneEffects ]:
                if gs in geneTerms.g2T:
                    vSets|=set(geneTerms.g2T[gs])
            for s in vSets:
                allRes[s][tName].cnt +=1

    totals = { tName: len(vs) for tName,vs in testVarGenesDict }
    
    bcgTotal = totals['BACKGROUND']
    for s in geneTerms.t2G:
        bcgInSet = allRes[s]['BACKGROUND'].cnt
        if bcgInSet == 0:
            bcgInSet = 0.5
        backProb = float(bcgInSet)/bcgTotal

        for tName,vs in testVarGenesDict:
            res = allRes[s][tName]    
            total = totals[tName]

            res.pVal = p = stats.binom_test(res.cnt, total, p=backProb)
            res.expected = round(backProb*total, 4)

    for tName,vs in testVarGenesDict:
        sp = [ (s, trs[tName].pVal) for s,trs in allRes.items() ]
        qVals = computeQVals([x[1] for x in sp])
        for a,qVal in zip(sp,qVals):
            allRes[a[0]][tName].qVal = qVal

    return allRes, totals
                                
def computeQVals(pVals):
    ss = sorted([(i,p) for i,p in enumerate(pVals)], key=lambda x: x[1])
    qVals = [ip[1]*len(ss)/(j+1) for j,ip in enumerate(ss)];
    qVals = [q if q<=1.0 else 1.0 for q in qVals]
    prevPVal = ss[-1][1]
    prevQVal = qVals[-1]
    for i in xrange(len(ss)-2,-1,-1):
        if ss[i][1] == prevPVal:
            qVals[i] = prevQVal
        else:
            prevPVal = ss[i][1]
            prevQVal = qVals[i]
    return [ q  for d,q in sorted(zip(ss,qVals), key=lambda x: x[0][0])]

def printSummaryTable(testVarGenesDict, geneTerms,allRes,totals):
    tTests = [tn for tn,vs in testVarGenesDict if tn != "BACKGROUND"]
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

def fltVs(vs):
    ret = []
    seen = set()
    for v in vs:
        hasNew = False
        for ge in v.requestedGeneEffects:
            sym = ge['sym']
            kk = v.familyId + "." + sym
            if kk not in seen:
                hasNew = True
            seen.add(kk)
        if hasNew:
            ret.append(v) 
    return ret

def oneVariantPerRecurrent(vs):
    gnSorted = sorted([[ge['sym'], v] for v in vs for ge in v.requestedGeneEffects ]) 
    sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
    sym2FN = { sym: len(set([v.familyId for v in vs])) for sym, vs in sym2Vars.items() } 
    return [x[0] for x in sym2Vars.values() if len(x)>1]


def denovoSets(dnvStds):
    r = GeneTerms()
    r.geneNS = "sym"

    def addSet(setname, genes):
        r.tDesc[setname] = setname
        for gSym in genes:
            r.t2G[setname][gSym]+=1
            r.g2T[gSym][setname]+=1
    def genes(inChild,effectTypes,inGenesSet=None):
        if inGenesSet:
            vs = vDB.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild,geneSyms=inGenesSet)
        else:
            vs = vDB.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild)
        return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}

    def set_genes(geneSetDef):
        gtId,tmId = geneSetDef.split(":")
        return set(giDB.getGeneTerms(gtId).t2G[tmId].keys())

    def recGenes(inChild,effectTypes):
        vs = vDB.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild)

        gnSorted = sorted([[ge['sym'], v] for v in vs for ge in v.requestedGeneEffects ]) 
        sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
        sym2FN = { sym: len(set([v.familyId for v in vs])) for sym, vs in sym2Vars.items() } 
        return {g for g,nf in sym2FN.items() if nf>1 }

    addSet("recPrbLGDs",     recGenes('prb' ,'LGDs'))

    addSet("prbLGDs",           genes('prb' ,'LGDs'))
    addSet("prbMaleLGDs",       genes('prbM','LGDs'))
    addSet("prbFemaleLGDs",     genes('prbF','LGDs'))
    addSet("prbLGDsInFMR1",     genes('prb','LGDs',set_genes("main:FMR1-targets")))

    addSet("prbLGDsInCHDs",     genes('prb','LGDs',set("CHD1,CHD2,CHD3,CHD4,CHD5,CHD6,CHD7,CHD8,CHD9".split(','))))

    addSet("prbMissense",       genes('prb' ,'missense'))
    addSet("prbMaleMissense",   genes('prb' ,'missense'))
    addSet("prbFemaleMissense", genes('prb' ,'missense'))
    addSet("prbSynonymous",     genes('prb' ,'synonymous'))

    addSet("sibLGDs",           genes('sib' ,'LGDs'))
    addSet("sibMissense",       genes('sib' ,'missense'))
    addSet("sibSynonymous",     genes('sib' ,'synonymous'))

    return r
    

if __name__ == "__main__":
    # setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/miRNA-TargetScan6.0-Conserved'
    # setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/GeneSets'

    setsFile = "main"
    denovoStudies = "allWE"
    transmittedStudy = "wig781"

    if len(sys.argv)>1:
        setsFile=sys.argv[1]

    if setsFile=='denovo':
        # geneTerms = denovoSets(denovoStudies)
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

    testVarGenesDict = [
        ['De novo recPrbLGDs',             oneVariantPerRecurrent(vDB.get_denovo_variants(dnvSts,inChild='prb',  effectTypes="LGDs"))],
        ['De novo prbLGDs',                fltVs(vDB.get_denovo_variants(dnvSts,inChild='prb',  effectTypes="LGDs"))],
        ['De novo prbMaleLGDs',            fltVs(vDB.get_denovo_variants(dnvSts,inChild='prbM', effectTypes="LGDs"))],
        ['De novo prbFemaleLGDs',          fltVs(vDB.get_denovo_variants(dnvSts,inChild='prbF', effectTypes="LGDs"))],
        ['De novo sibLGDs',                fltVs(vDB.get_denovo_variants(dnvSts,inChild='sib',  effectTypes="LGDs"))],
        ['De novo sibMaleLGDs',            fltVs(vDB.get_denovo_variants(dnvSts,inChild='sibM', effectTypes="LGDs"))],
        ['De novo sibFemaleLGDs',          fltVs(vDB.get_denovo_variants(dnvSts,inChild='sibF', effectTypes="LGDs"))],
        ['De novo prbMissense',            fltVs(vDB.get_denovo_variants(dnvSts,inChild='prb',  effectTypes="missense"))],
        ['De novo prbMaleMissense',        fltVs(vDB.get_denovo_variants(dnvSts,inChild='prbM',  effectTypes="missense"))],
        ['De novo prbFemaleMissense',      fltVs(vDB.get_denovo_variants(dnvSts,inChild='prbF',  effectTypes="missense"))],
        ['De novo sibMissense',            fltVs(vDB.get_denovo_variants(dnvSts,inChild='sib',  effectTypes="missense"))],
        ['De novo prbSynonymous',          fltVs(vDB.get_denovo_variants(dnvSts,inChild='prb',  effectTypes="synonymous"))],
        ['De novo sibSynonymous',          fltVs(vDB.get_denovo_variants(dnvSts,inChild='sib',  effectTypes="synonymous"))],
        
        ['UR LGDs in parents',             list(transmStdy.get_transmitted_summary_variants(ultraRareOnly=True, effectTypes="LGDs"))],
        ['BACKGROUND',                     list(transmStdy.get_transmitted_summary_variants(ultraRareOnly=True, effectTypes="synonymous"))]
    ]

    print >> sys.stderr, "Running the test..."
    allRes, totals = enrichmentTest(testVarGenesDict, geneTerms)

    print >> sys.stderr, "Preparing the summary table..."
    printSummaryTable(testVarGenesDict,geneTerms,allRes,totals)

    print >> sys.stderr, "Done!"
    
