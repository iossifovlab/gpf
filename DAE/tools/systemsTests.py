#!/bin/env python

from DAE import *
from WeightedSample import WeightedSample
from collections import defaultdict
from tfidf import GetTFIDFMatrix 
from omnibus import GetOmnibusMatrix
from MatrixClass import *

import numpy as np
from os.path import basename
from os.path import splitext 
import glob

class PPINetwork:
    def __init__(self, fn): 
        self.name = splitext(basename(fn))[0]
        self.nodes = {}
        self.nbrs = defaultdict(lambda : defaultdict(int))
        f = open(fn)
        for l in f:
            gis = l.strip().split('\t')
            if len(gis)!=2:
                raise Exception("Wrong line in " + fn)
            g1Id,g2Id = gis
            if g1Id==g2Id:
                continue
            self.nbrs[g1Id][g2Id]+=1
            self.nbrs[g2Id][g1Id]+=1
        f.close()
        propsFn = splitext(fn)[0]+"-nodeProps.txt"
        pf = open(propsFn)
        pf.readline()
        for l in pf:
            cs = l.strip().split('\t')
            if len(cs) != 4:
                raise Excpetion("Worng line in " + propsFn)
            nId, degree, betweennes, clustCoef = cs
            class NodeProps:
                pass
            nps = NodeProps()
            nps.nId = nId
            nps.degree = len(self.nbrs[nId]) 
            nps.degreeP = int(degree) 
            nps.betweennes = float(betweennes)
            nps.clustCoef = float(clustCoef)
            self.nodes[nId] = nps
        pf.close()
       
        intersection = set(self.nodes) & set(self.nbrs) 
        if len(intersection) != len(self.nodes) or len(intersection) != len(self.nbrs):
            raise Excpetion('The network and the node properties do not match')

    def nInternalInters(self,nodeSubset):
        return len([1 for nd in nodeSubset for nbr in self.nbrs[nd] if nbr in nodeSubset])
            

def weightedNetworkNodeDegrees(m):
    return { g:w for g,w in zip(m.geneIndexToId, m.GetWeightedNodeDegrees()) } 


def prepareGeneTerms(name):
    class GTS:
        pass

    gts = GTS()
    gts.name = name
    gts.geneTerms = giDB.getGeneTerms(gts.name, inNS='id')
    aaaFixMe = [(g,ts.keys()) for g,ts in gts.geneTerms.g2T.items()]

    gts.tfidfM = GetTFIDFMatrix(aaaFixMe)
    gts.tfidfWNDegree = weightedNetworkNodeDegrees(gts.tfidfM) 

    gts.omniM = GetOmnibusMatrix(aaaFixMe)
    gts.omniWNDegree = weightedNetworkNodeDegrees(gts.omniM) 

    geneTermsStrs.append(gts)
    return gts

def prepareWeightedNetwork(netF): 
    print >>sys.stderr, "Loading", netF,"..."
    class WNT:
        pass

    wnt = WNT()
    wnt.name = splitext(basename(netF))[0]
    wnt.wn = Matrix(netF)
    wnt.nodeDegrees = weightedNetworkNodeDegrees(wnt.wn) 

    weightedNetworks.append(wnt)

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
            if rScr >= realScr:
                ts.nBigger+=1
        ts.pVal = float(ts.nBigger)/Iter
        if ts.nBigger > 4 and ts.nBigger < Iter - 4:
            return ts
    return ts

def runPpnScTest(testGroup, testName, vls, geneWeights, ppn):
    sbWghts = {g:w for g,w in geneWeights.items() if g in ppn.nodes} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in vls.genes if x in sbWghts]

    if len(gns)==0:
        print testGroup, testName, vls.name, "Empty gene set"
        return

    def scrF(gis):
        return ppn.nInternalInters(gis)

    tr = runATest(scrF,gns,ws)

    saveTestR(testGroup, testName, vls.name, tr)

def runWnScTest(testGroup, testName, vls, geneWeights, wn):
# def SMCTest(wn, propName, geneIds, Iter=1000):
    sbWghts = {g:w for g,w in geneWeights.items() if g in wn.geneIdToIndex} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in vls.genes if x in sbWghts]

    if len(gns)==0:
        print testGroup, testName, vls.name, "Empty gene set"
        return

    def scrF(gis):
        return wn.GetSubNetworkIvan(gis).mean()

    tr = runATest(scrF,gns,ws)

    saveTestR(testGroup, testName, vls.name, tr)


def runNumberTest(testGroup, testName, vls, geneWeights, numbers, defaultVal=None):

    testGenes = set(geneWeights.keys()) & set(numbers.keys())
    vals = {x:numbers[x] for x in testGenes}
    wghts = {g:w for g,w in geneWeights.items() if g in testGenes}
    gns = {g:n for g,n in vls.genes.items() if g in testGenes}

    if len(gns)==0:
        print testGroup, testName, vls.name, "Empty gene set"
        return

    def scrF(gs):
        return float(sum(vals[g] for g in gs))/len(gs)

    ws = WeightedSample(wghts)

    tr = runATest(scrF,gns,ws)
    tr.ntWeigths = wghts 
    tr.ntVals = vals 
    tr.ntSubset = gns 

    saveTestR(testGroup, testName, vls.name, tr)

    if defaultVal==None:
        return

    testGenesD = geneWeights.keys()
    valsD = {x:numbers[x] if x in numbers else 0 for x in testGenesD }
    wghtsD = {g:w for g,w in geneWeights.items() if g in testGenesD}
    gnsD = {g:n for g,n in vls.genes.items() if g in testGenesD }

    def scrFD(gs):
        return float(sum(valsD[g] for g in gs))/len(gs)
    wsD = WeightedSample(wghtsD)

    trD = runATest(scrFD,gnsD,wsD)
    trD.ntWeigths = wghtsD 
    trD.ntVals = valsD 
    trD.ntSubset = gnsD 

    saveTestR(testGroup, testName+"-D", vls.name, trD)
    

def saveTestR(testGroup,testName,variantListName, tsr):
    rscrs = np.array(tsr.randScrs)
    key = "-".join((testGroup, testName, variantListName))
    testResults[key] = tsr
    print tsr.pVal, testGroup, testName, variantListName, tsr.Iter, tsr.realScr, rscrs.mean(), rscrs.std() 

def procPPN(ppn,vls,geneWeights):
    runNumberTest("PPN." + ppn.name, "degree",  vls, geneWeights, {ni.nId:ni.degree for ni in ppn.nodes.values()} ) 
    runNumberTest("PPN." + ppn.name, "betweennes",  vls, geneWeights, {ni.nId:ni.betweennes for ni in ppn.nodes.values()} ) 
    runNumberTest("PPN." + ppn.name, "clustCoef",  vls, geneWeights, {ni.nId:ni.clustCoef for ni in ppn.nodes.values()} ) 
    runPpnScTest("PPN." + ppn.name, "SVC",  vls, geneWeights, ppn)


def procWN(wnt,vls,geneWeights):
    runWnScTest("WN." + wnt.name, "SVC",  vls, geneWeights, wnt.wn)
    runNumberTest("WN." + wnt.name, "degree",  vls, geneWeights, wnt.nodeDegrees)

def procGT(gts,vls,geneWeights):
    numbers = {g:sum([1 for tnum in gts.geneTerms.g2T[g].values()]) for g in gts.geneTerms.g2T }

    runNumberTest("GT." + gts.name, "nTerms", vls, geneWeights, numbers, 0)
    runNumberTest("GT." + gts.name, "tfidfDegree", vls, geneWeights, gts.tfidfWNDegree)
    runNumberTest("GT." + gts.name, "omniDegree", vls, geneWeights, gts.omniWNDegree)

    runWnScTest("GT." + gts.name, "tfidfClust",  vls, geneWeights, gts.tfidfM)
    runWnScTest("GT." + gts.name, "omniClust",  vls, geneWeights, gts.omniM)

    '''
    # no 'no-terms' genes
    testGenes = set(geneWeights.keys()) & set(gts.geneTerms.g2T.keys())
    vals = {x:sum([1 for y in gts.geneTerms.g2T[x].values()]) for x in testGenes}
    wghts = {g:w for g,w in geneWeights.items() if g in testGenes}
    gns = {g:n for g,n in vls.genes.items() if g in testGenes}

    saveTestR("GT." + gts.name, "nTermNo0", vls.name, runNumberTest(wghts,vals,gns))

    # with 'no-terms' genes
    testGenes = geneWeights.keys()
    vals = {x:sum([1 for y in gts.geneTerms.g2T[x].values()]) if x in gts.geneTerms.g2T else 0 for x in testGenes }
    gns = {g:n for g,n in vls.genes.items() if g in testGenes}

    saveTestR("GT." + gts.name, "nTermWith0", vls.name, runNumberTest(geneWeights,vals,gns))
    '''

def drawNumberTestData(trName):
    tr = testResults[trName]
    figure()
    c = Counter(tr.ntVals.values())
    plot(c.keys(), c.values())
    # hist(tr.ntVals.values(),1000)
    plot([tr.ntVals[x] for x in tr.ntSubset],1.0 + randn(len(tr.ntSubset))*max(c.values())/100.0,'ro')


    
if __name__ == "__main__":
    '''
    weightedNetworks = []
    prepareWeightedNetwork('/data/safe/ecicek/Workspace6/Matrix/Sarah/Integrated/sarah.npz') 
    for f in glob.glob('/data/safe/ecicek/Workspace6/Matrix/Sarah/*.npz'):
        prepareWeightedNetwork(f)

    geneTermsStrs = []
    prepareGeneTerms('miRNA') 
    prepareGeneTerms('domain') 
    prepareGeneTerms('GO') 
    '''

    
    variantLists = [] 
    vls = prepareVariantList("autLGDs", vDB.get_denovo_variants('allWEandTG',effectTypes="LGDs",inChild="prb"))
    # variantLists = [] 
    recurrentVariantList("autLGDsRec", vls)
    prepareVariantList("autMis", vDB.get_denovo_variants('allWEandTG',effectTypes="missense",inChild="prb"))
    # prepareVariantList("autSyn", vDB.get_denovo_variants('allWEandTG',effectTypes="synonymous",inChild="prb"))
    # prepareVariantList("sibLGDs", vDB.get_denovo_variants('allWEandTG',effectTypes="LGDs",inChild="sib"))
    giDB.fprops
    
    nullWeightId = 'refSeqCodingInTargetLen'
    geneWeights = {id:gi.fprops[nullWeightId] for id,gi in giDB.genes.items() if nullWeightId in gi.fprops}

    testResults = {}
    '''
    for wnt in weightedNetworks:
        for vls in variantLists:
            procWN(wnt,vls,geneWeights)
    for gts in geneTermsStrs:
        for vls in variantLists:
            procGT(gts,vls,geneWeights)
    '''
    '''
    for gts in geneTermsStrs:
        gnIds = gts.geneTerms.g2T.keys()
        dgs = np.array([(len(gts.geneTerms.g2T[x]), gts.tfidfWNDegree[x], gts.omniWNDegree[x]) for x in gnIds])
        ccs =  np.corrcoef(dgs.T)
        print gts.name, ccs[0,1], ccs[0,2], ccs[1,2]
    ''' 
    for vls in variantLists:
        for f in glob.glob('/home/iossifov/work/T115/PPI/*-ppimap.txt'):
            procPPN(PPINetwork(f),vls,geneWeights)


    # for g,n in variantLists[0].genes.items(): 
    #     if giDB.genes[g].sym in cc.t2G['BRK']:
    #         print giDB.genes[g].sym,n
 

