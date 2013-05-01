#!/bin/env python

from DAE import *
from WeightedSample import WeightedSample
from collections import defaultdict
from tfidf import GetTFIDFMatrix 
from omnibus import GetOmnibusMatrix

import numpy as np

def prepareGeneTerms(name):
    class GTS:
        pass

    gts = GTS()
    gts.name = name
    gts.geneTerms = giDB.getGeneTerms(gts.name, inNS='id')
    aaaFixMe = [(g,ts.keys()) for g,ts in gts.geneTerms.g2T.items()]

    def wndF(m):
        return { g:w for g,w in zip(m.geneIndexToId, m.GetWeightedNodeDegrees()) } 

    gts.tfidfM = GetTFIDFMatrix(aaaFixMe)
    gts.tfidfWNDegree = wndF(gts.tfidfM) 

    gts.omniM = GetOmnibusMatrix(aaaFixMe)
    gts.omniWNDegree = wndF(gts.omniM) 

    geneTermsStrs.append(gts)
    return gts


def recurrentVariantList(name, fromVls):
    class VLS:
        pass
    vls = VLS()
    vls.name = name
    
    vls.genes = { g:n for g,n in fromVls.genes.items() if n>1 }
    vls.genesSym = { g:n for g,n in fromVls.genesSym.items() if n>1 }
  
    variantLists.append(vls)
    return vls
    

def prepareVariantList(name,vs):
    class VLS:
        pass
    vls = VLS()
    vls.name = name
    
    geneSymFamily = defaultdict(lambda : defaultdict(int))
    for v in vs:
        for ge in v.requestedGeneEffects:
            geneSymFamily[ge['sym']][v.familyId]+=1
    vls.genesSym = { g:len(fms) for g,fms in geneSymFamily.items() }
    vls.genes = { giDB.getCleanGeneId("sym",g):n for g,n in vls.genesSym.items() if giDB.getCleanGeneId("sym",g) }
  
    variantLists.append(vls)
    return vls
    
def runATest(scrF,gs,ws,withReplacement=False):
    realScr = scrF(gs)
    N = len(gs)

    if withReplacement:
        N = sum([x for x in gs.values()])

    class TestResult:
        pass

    for Iter in [100,1000,10000]:
        ts = TestResult()
        ts.nBigger = 0
        ts.randScrs = []
        ts.Iter = Iter
        ts.realScr = realScr

        for i in xrange(Iter):
            if withReplacement:
                rScr = scrF(ws.getWithReplacement(N))
            else:
                rScr = scrF(ws.getWithoutReplacement(N))
            ts.randScrs.append(rScr)
            if rScr > realScr:
                ts.nBigger+=1
        ts.pVal = float(ts.nBigger)/Iter
        if ts.nBigger > 4 and ts.nBigger < Iter - 4:
            return ts
    return ts

def runNumberTest(weights,vals,subset):
    ws = WeightedSample(weights)
    def scrF(gs):
        return float(sum(vals[g] for g in gs))/len(gs)
    return runATest(scrF,subset,ws)

def saveTestR(testGroup,testName,variantListName, tsr):
    rscrs = np.array(tsr.randScrs)
    print tsr.pVal, testGroup, testName, variantListName, tsr.pVal, tsr.Iter, tsr.realScr, rscrs.mean(), rscrs.std() 

def procGT(gts,vls,geneWeights):
    # no 'no-terms' genes
    testGenes = set(geneWeights.keys()) & set(gts.geneTerms.g2T.keys())
    vals = {x:len(gts.geneTerms.g2T[x]) for x in testGenes}
    wghts = {g:w for g,w in geneWeights.items() if g in testGenes}
    gns = {g:n for g,n in vls.genes.items() if g in testGenes}

    saveTestR("GT." + gts.name, "nTermNo0", vls.name, runNumberTest(wghts,vals,gns))

    # with 'no-terms' genes
    testGenes = geneWeights.keys()
    vals = {x:len(gts.geneTerms.g2T[x]) if x in gts.geneTerms.g2T else 0 for x in testGenes }
    gns = {g:n for g,n in vls.genes.items() if g in testGenes}

    tstR = runNumberTest(geneWeights,vals,gns)
    saveTestR("GT." + gts.name, "nTermWith0", vls.name, runNumberTest(wghts,vals,gns))


if __name__ == "__main__":
    '''
    geneTermsStrs = []
    variantLists = [] 

    prepareGeneTerms('miRNA') 
    prepareGeneTerms('domain') 
    prepareGeneTerms('GO') 

    vls = prepareVariantList("autLGDs", vDB.get_denovo_variants('all',effectTypes="LGDs",inChild="prb"))
    recurrentVariantList("autLGDsRec", vls)
    giDB.fprops
    
    nullWeightId = 'refSeqCodingInTargetLen'
    geneWeights = {id:gi.fprops[nullWeightId] for id,gi in giDB.genes.items() if nullWeightId in gi.fprops}
    '''

    # for gts in geneTermsStrs:
    #     for vls in variantLists:
    #         procGT(gts,vls,geneWeights)

    for gts in geneTermsStrs:
        gnIds = gts.geneTerms.g2T.keys()
        dgs = np.array([(len(gts.geneTerms.g2T[x]), gts.tfidfWNDegree[x], gts.omniWNDegree[x]) for x in gnIds])
        ccs =  np.corrcoef(dgs.T)
        print gts.name, ccs[0,1], ccs[0,2], ccs[1,2]

    # for g,n in variantLists[0].genes.items(): 
    #     if giDB.genes[g].sym in cc.t2G['BRK']:
    #         print giDB.genes[g].sym,n
 

