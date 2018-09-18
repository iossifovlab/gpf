#!/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from builtins import zip
from builtins import range
from past.utils import old_div
from builtins import object
from DAE import *
from WeightedSample import WeightedSample
from tfidf import GetTFIDFMatrix 
from omnibus import GetOmnibusMatrix
from MatrixClass import *
from ExpressionData import load_expression_data_bin
from MicroarrayTest import ConverttoNums
from GeneTerms import loadGeneTerm

import numpy as np
from collections import defaultdict
from os.path import basename
from os.path import splitext 
import glob
import copy
import sys
import scipy 
import pickle



# randIterss = [100,1000,10000]
randIterss = [1000]

class PPINetwork(object):
    def __init__(self, fn=None, ppn=None):
        if fn:
            self._load_from_file(fn)
        if ppn:
            self.geneNS = ppn.geneNS
            self.name = ppn.name
            self.nbrs = copy.deepcopy(ppn.nbrs)
            self.nodes = copy.deepcopy(ppn.nodes)
            
    def shuffle(self):
        es = [[a,b] for a in self.nbrs for b in self.nbrs[a] if a<b]
        # print "0:",len(es)
        np.random.shuffle(es)
        es = [[a,b] if r < 0.5 else [b,a] for r,(a,b) in zip(np.random.rand(len(es)),es)]
        # print "OO:", " ".join([a+b for a,b in es])
        # print "1:",len(es)


        E = len(es)
        i = 0
       
        newNbrs = defaultdict(lambda : defaultdict(int))
        processedI = set()

        def proc(i):
            # if es[i][0] == es[i][1]:
            #     x10
            # 
            # if es[i][1] in newNbrs[es[i][0]]:
            #     x10

            newNbrs[es[i][0]][es[i][1]]+=1
            newNbrs[es[i][1]][es[i][0]]+=1
            processedI.add(i)

        def swap(i,j):
            def intS(i):
                e = es[i]
                return e[0]+"-"+e[1] if e[0] < e[1] else e[1]+"-"+e[0]
            # print "Swap attempt: i: %d, j: %d [%s <-> %s]" % (i,j,intS(i),intS(j)),
            if len(set(es[i]+es[j]))!=4:
                # print "FAIL 1"
                return False 

            if es[i][0] not in newNbrs[es[j][0]] and es[i][1] not in newNbrs[es[j][1]]:
                es[i][1],es[j][0] = es[j][0],es[i][1] 
                proc(i)
                proc(j)
                # print "Success 2: [%s <-> %s]" % (intS(i),intS(j))
                return True

            if es[i][0] not in newNbrs[es[j][1]] and es[i][1] not in newNbrs[es[j][0]]:
                es[i][1],es[j][1] = es[j][1],es[i][1] 
                proc(i)
                proc(j)
                # print "Success 1: [%s <-> %s]" % (intS(i),intS(j))
                return True


            # print "FAIL 2"
            return False
        
        for i in range(E):
            if i in processedI:
                continue
            for j in range(i+1,E):
                if j in processedI:
                    continue
                
                if swap(i,j):
                    break
            if i not in processedI:
                if es[i][0] in newNbrs[es[i][1]]:
                    for j in range(E):
                        if swap(i,j):
                            break
                else:
                    proc(i)
               
        # print "2:",len(es)

        # print "failed:", failed, "/", E
        self.nbrs = newNbrs

        # print "at the end:", len([[a,b] for a in self.nbrs for b in self.nbrs[a] if a<b])
        
    def _load_from_file(self,fn):
        self.geneNS = "id"
        self.name = splitext(basename(fn))[0]
        self.nodes = {}
        self.nbrs = defaultdict(lambda : defaultdict(int))
        f = open(fn)
        for l in f:
            if l[0] == "#":
                if l.startswith("# geneNS: "):
                    self.geneNS = l.strip()[len("# geneNS: "):]
                continue
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
            if nId not in self.nbrs:
                # print "AAAAA",cs 
                continue
            class NodeProps(object):
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

    def nBetweenInters(self,nodesA,nodesB):
        nodesBS = set(nodesB)
        return sum([len(nodesBS & set(self.nbrs[x])) for x in nodesA])

def run_a_test(scrF,gs,ws,withReplacement=False):
    realScr = scrF(gs)
    N = len(gs)

    if withReplacement:
        N = sum([x for x in list(gs.values())])

    class TestResult(object):
        pass

    # for Iter in [100,1000,10000]:
    for Iter in randIterss:
        ts = TestResult()
        ts.nBigger = 0
        ts.randScrs = []
        ts.Iter = Iter
        ts.realScr = realScr

        for i in range(Iter):
            if withReplacement:
                rScr = scrF(ws.getWithReplacement(N))
            else:
                rScr = scrF(ws.getWithoutReplacement(N))
            ts.randScrs.append(rScr)
            if rScr >= realScr:
                ts.nBigger+=1
        ts.pVal = old_div(float(ts.nBigger),Iter)
        if ts.nBigger > 4 and ts.nBigger < Iter - 4:
            return ts
    return ts


sss = defaultdict(list)

def getRandNets(ppn,n):
    rr = sss[ppn]
    if len(rr)==0:
        prevS = ppn
    else:
        prevS = rr[-1] 

    while len(rr) < n:
        prevS = PPINetwork(ppn=prevS)
        prevS.shuffle()
        rr.append(prevS)
        print("built ", len(rr), "rand networks")
    return rr[0:n]
            
        
        
def run_a_PPI_shuffle_test(scrF,ppn):
    realScr = scrF(ppn)

    class TestResult(object):
        pass

    ppnS = PPINetwork(ppn=ppn)

    # for Iter in [100,1000,10000]:
    for Iter in randIterss: 
    # for Iter in [100]:
        print("Runniter with Iter:", Iter)
        ts = TestResult()
        ts.nBigger = 0
        ts.randScrs = []
        ts.Iter = Iter
        ts.realScr = realScr

        for ppnS in getRandNets(ppn,Iter):
            rScr = scrF(ppnS)
            ts.randScrs.append(rScr)
            if rScr >= realScr:
                ts.nBigger+=1
        ts.pVal = old_div(float(ts.nBigger),Iter)
        if ts.nBigger > 4 and ts.nBigger < Iter - 4:
            return ts
    return ts

def run_in_set_test(genes, geneWeights, inSet):
    sbWghts = geneWeights
    ws = WeightedSample(sbWghts)
    gns = [x for x in genes if x in sbWghts]

    if len(gns)==0:
        return

    def scrF(gis):
        return len(set(gis) & set(inSet))

    return run_a_test(scrF,gns,ws)

def run_ppn_sc_test(genes, geneWeights, ppn):
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in ppn.nodes} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in genes if x in sbWghts]

    if len(gns)==0:
        return

    def scrF(gis):
        return ppn.nInternalInters(gis)

    return run_a_test(scrF,gns,ws)

def run_ppn_sc_shuffle_test(genes, ppn):
    gns = [x for x in genes if x in ppn.nodes]

    if len(gns)==0:
        print('hahaha')
        return

    def scrF(ppn):
        return ppn.nInternalInters(gns)

    return run_a_PPI_shuffle_test(scrF,ppn)

def run_ppn_link_test(genesFixed, genes, geneWeights, ppn):
    genesFixedS = {g for g in genesFixed if g in ppn.nodes} 
    if len(genesFixedS)==0:
        return
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in ppn.nodes and g not in genesFixedS} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in genes if x in sbWghts and x not in genesFixedS]

    if len(gns)==0:
        return

    def scrF(gis):
        return ppn.nBetweenInters(genesFixedS,gis)

    return run_a_test(scrF,gns,ws)

def run_ppn_link_shuffle_test(genesFixed, genes, ppn):
    genesFixedS = {g for g in genesFixed if g in ppn.nodes} 
    if len(genesFixedS)==0:
        return
    gns = [x for x in genes if x in ppn.nodes and x not in genesFixedS]
    if len(gns)==0:
        return

    def scrF(ppn):
        return ppn.nBetweenInters(genesFixedS,gns)

    return run_a_PPI_shuffle_test(scrF,ppn)

def run_wn_sc_test(genes, geneWeights, wn):
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in wn.geneIdToIndex} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in genes if x in sbWghts]

    if len(gns)==0:
        return

    def scrF(gis):
        return wn.GetSubNetworkIvan(gis).mean()

    return run_a_test(scrF,gns,ws)

def run_wn_link_test(genesFixed, genes, geneWeights, wn):
    genesFixedS = {g for g in genesFixed if g in wn.geneIdToIndex } 
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in wn.geneIdToIndex and g not in genesFixedS} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in genes if x in sbWghts and x not in genesFixedS]

    if len(gns)==0:
        return

    def scrF(gis):
        return wn.GetBetweenWeights(genesFixedS,gis).mean()

    return run_a_test(scrF,gns,ws)


def run_number_test(genes, geneWeights, numbers, defaultVal=None):

    testGenes = set(geneWeights.keys()) & set(numbers.keys())
    vals = {x:numbers[x] for x in testGenes}
    wghts = {g:w for g,w in list(geneWeights.items()) if g in testGenes}
    gns = {g:n for g,n in list(genes.items()) if g in testGenes}

    if len(gns)==0:
        return

    def scrF(gs):
        return old_div(float(sum(vals[g] for g in gs)),len(gs))

    ws = WeightedSample(wghts)

    return run_a_test(scrF,gns,ws)

    '''
    if defaultVal==None:
        return

    testGenesD = geneWeights.keys()
    valsD = {x:numbers[x] if x in numbers else 0 for x in testGenesD }
    wghtsD = {g:w for g,w in geneWeights.items() if g in testGenesD}
    gnsD = {g:n for g,n in genes.items() if g in testGenesD }

    def scrFD(gs):
        return float(sum(valsD[g] for g in gs))/len(gs)
    wsD = WeightedSample(wghtsD)

    trD = run_a_test(scrFD,gnsD,wsD)
    '''


class FunctionalProfiler(object):
    def __init__(self,denovoStudies='allWE',geneWeightProp='refSeqCodingInTargetLen'):
        giDB.fprops
        self._geneWeightsId = {id:gi.fprops[geneWeightProp] for id,gi in list(giDB.genes.items()) if geneWeightProp in gi.fprops}
        self._geneWeightsSym = {gi.sym:gi.fprops[geneWeightProp] for gi in list(giDB.genes.values()) if geneWeightProp in gi.fprops}
        self.geneSets = vDB.get_denovo_sets(denovoStudies)
        # self.toGeneSets = ['recPrbLGDs', 'sinPrbLGDs']
        self.toGeneSets = ['prb.LoF.Recurrent', 'prb.LoF.Single']
   
    def get_sets_and_weights(self,ns='sym'):
        if ns=='sym':
            return self.geneSets,self._geneWeightsSym 
        elif ns=='id':
            gsID = copy.deepcopy(self.geneSets)
            gsID.renameGenes("id", lambda x: giDB.getCleanGeneId("sym", x))
            return gsID,self._geneWeightsId
        else:
            raise Exception('Unknown name space: ' + ns)
        
    def profile_wn(self,wn, ns='id'):
        gSets,gWghts = self.get_sets_and_weights(ns)
        nodeDegrees = weightedNetworkNodeDegrees(wn) 
        
        fpRes = defaultdict(dict)
        for gsN,gsGs in list(gSets.t2G.items()): 

            print(gsN,'sc ...', file=sys.stderr)
            fpRes[gsN]['sc'] = run_wn_sc_test(gsGs, gWghts, wn)

            print(gsN,'degree ...', file=sys.stderr)
            fpRes[gsN]['degree'] = run_number_test(gsGs, gWghts, nodeDegrees)

            print(gsN,'inNet ...', file=sys.stderr)
            fpRes[gsN]['inNet'] = run_in_set_test(gsGs, gWghts, wn.geneIdToIndex)

            for fixedGenes in self.toGeneSets:
                print(gsN,fixedGenes,'...', file=sys.stderr)
                fpRes[gsN][fixedGenes] = run_wn_link_test(gSets.t2G[fixedGenes], gsGs, gWghts, wn)

        return fpRes


    def profile_gts(self,gts,metric='tfidf'):
        gSets,gWghts = self.get_sets_and_weights(gts.geneNS)

        termNumbers = {g:len(tms) for g,tms in list(gts.g2T.items()) }

        # an alternative that uses the multiplicity of the terms per gene
        # termNumbers = {g:sum(tms.values()) for g,tms in gts.g2T.items() }

        aaaFixMe = [(g,list(ts.keys())) for g,ts in list(gts.g2T.items())]

        if metric=='tfidf':
            wn = GetTFIDFMatrix(aaaFixMe)
        elif metric=='omni':
            wn = GetOmnibusMatrix(aaaFixMe)
        else:
            raise Exception('unknown metric:' + metrix)
        nodeDegrees = weightedNetworkNodeDegrees(wn) 

        fpRes = defaultdict(dict)
        for gsN,gsGs in list(gSets.t2G.items()): 

            print(gsN,'sc ...', file=sys.stderr)
            fpRes[gsN]['sc'] = run_wn_sc_test(gsGs, gWghts, wn)

            print(gsN,'termNumber...', file=sys.stderr)
            fpRes[gsN]['termNumber'] = run_number_test(gsGs, gWghts, termNumbers)

            print(gsN,'degree ...', file=sys.stderr)
            fpRes[gsN]['degree'] = run_number_test(gsGs, gWghts, nodeDegrees)

            print(gsN,'withTerms ...', file=sys.stderr)
            fpRes[gsN]['withTerms'] = run_in_set_test(gsGs, gWghts, wn.geneIdToIndex)

            for fixedGenes in self.toGeneSets:
                print(gsN,fixedGenes,'...', file=sys.stderr)
                fpRes[gsN][fixedGenes] = run_wn_link_test(gSets.t2G[fixedGenes], gsGs, gWghts, wn)

        return fpRes

    def profile_ppn(self,ppn,shuffle=False):
        gSets,gWghts = self.get_sets_and_weights(ppn.geneNS)

        fpRes = defaultdict(dict)
        for gsN,gsGs in list(gSets.t2G.items()): 

            print(gsN,'inNetwork...', file=sys.stderr)
            fpRes[gsN]['inNetwork'] = run_in_set_test(gsGs, gWghts, ppn.nodes )

            print(gsN,'degree ...', file=sys.stderr)
            fpRes[gsN]['degree'] = run_number_test(gsGs, gWghts, {ni.nId:ni.degree for ni in list(ppn.nodes.values())} )

            print(gsN,'betweennes ...', file=sys.stderr)
            fpRes[gsN]['betweennes'] = run_number_test(gsGs, gWghts, {ni.nId:ni.betweennes for ni in list(ppn.nodes.values())} )

            print(gsN,'clustCoef...', file=sys.stderr)
            fpRes[gsN]['clustCoef'] = run_number_test(gsGs, gWghts, {ni.nId:ni.clustCoef for ni in list(ppn.nodes.values())} )

            print(gsN,'sc ...', file=sys.stderr)
            if shuffle:
                fpRes[gsN]['sc'] = run_ppn_sc_shuffle_test(gsGs, ppn)
            else:
                fpRes[gsN]['sc'] = run_ppn_sc_test(gsGs, gWghts, ppn)

            for fixedGenes in self.toGeneSets:
                print(gsN,fixedGenes,'...', file=sys.stderr)
                if shuffle:
                    fpRes[gsN][fixedGenes] = run_ppn_link_shuffle_test(gSets.t2G[fixedGenes], gsGs, ppn)
                else:
                    fpRes[gsN][fixedGenes] = run_ppn_link_test(gSets.t2G[fixedGenes], gsGs, gWghts, ppn)
        return fpRes

    def profile_gene_scalar(self,scalar,keyNS='sym'):
        gSets,gWghts = self.get_sets_and_weights(keyNS)

        fpRes = defaultdict(dict)
        for gsN,gsGs in list(gSets.t2G.items()): 

            print(gsN,'inScalar...', file=sys.stderr)
            fpRes[gsN]['inScalar'] = run_in_set_test(gsGs, gWghts, scalar )

            print(gsN,'scalar...', file=sys.stderr)
            fpRes[gsN]['scalar'] = run_number_test(gsGs, gWghts, scalar)
        return fpRes


    def print_res_summary(self,f,res):
        allGeneSetsOrd = self.toGeneSets + sorted([s for s in self.geneSets.t2G if s not in self.toGeneSets])

        allTests = {x for trd in res for x in trd}

        specialTests = ['sc'] + self.toGeneSets       
        specialTests = [tn for tn in specialTests if tn in allTests]
        testOrder = specialTests + sorted([x for x in {t for gs in list(res.values()) for t in gs} if x not in specialTests])

        def tr_pval_s(tr):
            if not tr:
                return "    X     "
            if tr.pVal>0.05 and tr.pVal<0.95:
                return "          "
            return "%10.4f" % (tr.pVal)


        f.write("\t".join(["%20s" % " "] + ["%10s" % (x) for x in testOrder]) + "\n")
                  
        for gs in allGeneSetsOrd:
            f.write("\t".join(["%20s" % (gs)] + [tr_pval_s(res[gs][x]) for x in testOrder]) + "\n")
    
        

    '''
    def procPPN(ppn,vls,geneWeights):
        runNumberTest("PPN." + ppn.name, "degree",  vls, geneWeights, {ni.nId:ni.degree for ni in ppn.nodes.values()} ) 
        runNumberTest("PPN." + ppn.name, "betweennes",  vls, geneWeights, {ni.nId:ni.betweennes for ni in ppn.nodes.values()} ) 
        runNumberTest("PPN." + ppn.name, "clustCoef",  vls, geneWeights, {ni.nId:ni.clustCoef for ni in ppn.nodes.values()} ) 
        runPpnScTest("PPN." + ppn.name, "SVC",  vls, geneWeights, ppn)

    def procGT(gts,vls,geneWeights):
        numbers = {g:sum([1 for tnum in gts.geneTerms.g2T[g].values()]) for g in gts.geneTerms.g2T }

        runNumberTest("GT." + gts.name, "nTerms", vls, geneWeights, numbers, 0)
        runNumberTest("GT." + gts.name, "tfidfDegree", vls, geneWeights, gts.tfidfWNDegree)
        runNumberTest("GT." + gts.name, "omniDegree", vls, geneWeights, gts.omniWNDegree)

        runWnScTest("GT." + gts.name, "tfidfClust",  vls, geneWeights, gts.tfidfM)
        runWnScTest("GT." + gts.name, "omniClust",  vls, geneWeights, gts.omniM)
    '''

def weightedNetworkNodeDegrees(m):
    return { g:w for g,w in zip(m.geneIndexToId, m.GetWeightedNodeDegrees()) } 


def prepareGeneTerms(name):
    class GTS(object):
        pass

    gts = GTS()
    gts.name = name
    gts.geneTerms = giDB.getGeneTerms(gts.name, inNS='id')
    aaaFixMe = [(g,list(ts.keys())) for g,ts in list(gts.geneTerms.g2T.items())]

    gts.tfidfM = GetTFIDFMatrix(aaaFixMe)
    gts.tfidfWNDegree = weightedNetworkNodeDegrees(gts.tfidfM) 

    gts.omniM = GetOmnibusMatrix(aaaFixMe)
    gts.omniWNDegree = weightedNetworkNodeDegrees(gts.omniM) 

    geneTermsStrs.append(gts)
    return gts

def prepareWeightedNetwork(netF): 
    print("Loading", netF,"...", file=sys.stderr)
    class WNT(object):
        pass

    wnt = WNT()
    wnt.name = splitext(basename(netF))[0]
    wnt.wn = Matrix(netF)
    wnt.nodeDegrees = weightedNetworkNodeDegrees(wnt.wn) 

    weightedNetworks.append(wnt)

def recurrentVariantList(name, fromVls):
    class VLS(object):
        pass
    vls = VLS()
    vls.name = name
    
    vls.genes = { g:n for g,n in list(fromVls.genes.items()) if n>1 }
    vls.genesSym = { g:n for g,n in list(fromVls.genesSym.items()) if n>1 }
  
    variantLists.append(vls)
    return vls
    
def prepareVariantList(name,vs):
    class VLS(object):
        pass
    vls = VLS()
    vls.name = name
    
    geneSymFamily = defaultdict(lambda : defaultdict(int))
    for v in vs:
        for ge in v.requestedGeneEffects:
            geneSymFamily[ge['sym']][v.familyId]+=1
    vls.genesSym = { g:len(fms) for g,fms in list(geneSymFamily.items()) }
    vls.genes = { giDB.getCleanGeneId("sym",g):n for g,n in list(vls.genesSym.items()) if giDB.getCleanGeneId("sym",g) }
  
    variantLists.append(vls)
    return vls

class TestResult(object):
    pass
    
def runATest(scrF,gs,ws,withReplacement=False):
    realScr = scrF(gs)
    N = len(gs)

    if withReplacement:
        N = sum([x for x in list(gs.values())])


    for Iter in randIterss:
        ts = TestResult()
        ts.nBigger = 0
        ts.randScrs = []
        ts.Iter = Iter
        ts.realScr = realScr

        for i in range(Iter):
            if withReplacement:
                rScr = scrF(ws.getWithReplacement(N))
            else:
                rScr = scrF(ws.getWithoutReplacement(N))
            ts.randScrs.append(rScr)
            if rScr >= realScr:
                ts.nBigger+=1
        ts.pVal = old_div(float(ts.nBigger),Iter)
        if ts.nBigger > 4 and ts.nBigger < Iter - 4:
            return ts
    return ts

def runPpnScTest(testGroup, testName, vls, geneWeights, ppn):
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in ppn.nodes} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in vls.genes if x in sbWghts]

    if len(gns)==0:
        print(testGroup, testName, vls.name, "Empty gene set")
        return

    def scrF(gis):
        return ppn.nInternalInters(gis)

    tr = runATest(scrF,gns,ws)

    saveTestR(testGroup, testName, vls.name, tr)

def runWnScTest(testGroup, testName, vls, geneWeights, wn):
# def SMCTest(wn, propName, geneIds, Iter=1000):
    sbWghts = {g:w for g,w in list(geneWeights.items()) if g in wn.geneIdToIndex} 
    ws = WeightedSample(sbWghts)
    gns = [x for x in vls.genes if x in sbWghts]

    if len(gns)==0:
        print(testGroup, testName, vls.name, "Empty gene set")
        return

    def scrF(gis):
        return wn.GetSubNetworkIvan(gis).mean()

    tr = runATest(scrF,gns,ws)

    saveTestR(testGroup, testName, vls.name, tr)


def runNumberTest(testGroup, testName, vls, geneWeights, numbers, defaultVal=None):

    testGenes = set(geneWeights.keys()) & set(numbers.keys())
    vals = {x:numbers[x] for x in testGenes}
    wghts = {g:w for g,w in list(geneWeights.items()) if g in testGenes}
    gns = {g:n for g,n in list(vls.genes.items()) if g in testGenes}

    if len(gns)==0:
        print(testGroup, testName, vls.name, "Empty gene set")
        return

    def scrF(gs):
        return old_div(float(sum(vals[g] for g in gs)),len(gs))

    ws = WeightedSample(wghts)

    tr = runATest(scrF,gns,ws)
    tr.ntWeigths = wghts 
    tr.ntVals = vals 
    tr.ntSubset = gns 

    saveTestR(testGroup, testName, vls.name, tr)

    if defaultVal==None:
        return

    testGenesD = list(geneWeights.keys())
    valsD = {x:numbers[x] if x in numbers else 0 for x in testGenesD }
    wghtsD = {g:w for g,w in list(geneWeights.items()) if g in testGenesD}
    gnsD = {g:n for g,n in list(vls.genes.items()) if g in testGenesD }

    def scrFD(gs):
        return old_div(float(sum(valsD[g] for g in gs)),len(gs))
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
    print(tsr.pVal, testGroup, testName, variantListName, tsr.Iter, tsr.realScr, rscrs.mean(), rscrs.std()) 

def procPPN(ppn,vls,geneWeights):
    runNumberTest("PPN." + ppn.name, "degree",  vls, geneWeights, {ni.nId:ni.degree for ni in list(ppn.nodes.values())} ) 
    runNumberTest("PPN." + ppn.name, "betweennes",  vls, geneWeights, {ni.nId:ni.betweennes for ni in list(ppn.nodes.values())} ) 
    runNumberTest("PPN." + ppn.name, "clustCoef",  vls, geneWeights, {ni.nId:ni.clustCoef for ni in list(ppn.nodes.values())} ) 
    runPpnScTest("PPN." + ppn.name, "SVC",  vls, geneWeights, ppn)


def procWN(wnt,vls,geneWeights):
    runWnScTest("WN." + wnt.name, "SVC",  vls, geneWeights, wnt.wn)
    runNumberTest("WN." + wnt.name, "degree",  vls, geneWeights, wnt.nodeDegrees)

def procGT(gts,vls,geneWeights):
    numbers = {g:sum([1 for tnum in list(gts.geneTerms.g2T[g].values())]) for g in gts.geneTerms.g2T }

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
    c = Counter(list(tr.ntVals.values()))
    plot(list(c.keys()), list(c.values()))
    # hist(tr.ntVals.values(),1000)
    plot([tr.ntVals[x] for x in tr.ntSubset],1.0 + randn(len(tr.ntSubset))*max(c.values())/100.0,'ro')

if __name__ == "__main_test__":
    fp = FunctionalProfiler()
    geneWeightProp = 'refSeqCodingInTargetLen'

    scalar = {id:gi.fprops[geneWeightProp] for id,gi in list(giDB.genes.items()) if geneWeightProp in gi.fprops}

    fpRes = fp.profile_gene_scalar(scalar,'id')
    fp.print_res_summary(sys.stdout,fpRes)

if __name__ == "__main_test__":
    fp = FunctionalProfiler()
    gSets,gWghts = fp.get_sets_and_weights('id')

    def netProfile(ppn):
        return "%d %d %s" % (len(ppn.nbrs), len([(a,b) for a in ppn.nbrs for b in ppn.nbrs[a] if a < b]), ",".join(["%s:%d" % (n,len(ppn.nbrs[n])) for n in sorted(ppn.nbrs.keys())]))
    
    # ppn = PPINetwork("tPpn.txt")
    ppn = PPINetwork("/home/iossifov/work/T115/PPI/hprd-ppimap.txt")

    ppnProf = netProfile(ppn)
   
    ''' 
    cc = Counter()
    for i in xrange(100):
        print "SHUFFLEE"
        ppn.shuffle()
        if netProfile(ppn) != ppnProf:
            x10
        cc[" ".join(sorted([a+b for a in ppn.nbrs for b in ppn.nbrs[a] if a < b]))]+=1
    for n,c in cc.items():
        print n, c
    '''
    # ppn.shuffle()
    # ppnProfS = netProfile(ppn)
    # print ppnProf==ppnProfS

def drawTwoSets(s1,s2,gts,ppn):
    clf()
    def gSym(g):
        if gts.geneNS == 'sym':
            return g
        else:
            return giDB.genes[g].sym

    gs1S = set(gts.t2G[s1].keys())
    gs2S = set(gts.t2G[s2].keys())  

    gs1 = sorted(gs1S,key=gSym)
    gs1Ind = {g:i for i,g in enumerate(gs1)}

    gs2 = sorted(gs2S-gs1S,key=gSym) 
    gs2Ind = {g:i for i,g in enumerate(gs2)}

    gs3 = sorted(gs2S&gs1S,key=gSym) 
    gs3Ind = {g:i for i,g in enumerate(gs2)}

    print([gSym(g) for g in gs3])
    ddd = {'s1U'   : [gs1, gs1Ind, -10, old_div(len(gs1),2), 'right','s2U'],
           's2U'   : [gs2, gs2Ind,  10, old_div(len(gs2),2), 'left', 's1U'] }
           # 'common': [gs3, gs3Ind,  20, len(gs3)/2, 'left']}

    # for gs,sId,x,ha in zip([gs1,gs2,gs3],[s1,s2,'common'],[-10,10,20],['right','left','left']):
    for sId,(gs, gsIn,x,y0,ha,otherSId) in list(ddd.items()):
        otherGsInd = ddd[otherSId][1]
        otherX = ddd[otherSId][2]
        otherY0 = ddd[otherSId][3]

        y = y0
        totalInt2Other = 0
        for g in gs:
            sgn = 1.0
            if ha=='right':
                sgn = -1.0
            otherNbrs = [n for n in ppn.nbrs[g] if n in otherGsInd]
            int2Other = len(otherNbrs)
            intAll = len(ppn.nbrs[g])
            prcnt = 0.0
            if intAll>0:
                prcnt = 100.00 * int2Other / intAll
            
            
            plot([x,x+sgn*intAll/100.0],[y+0.2,y+0.2],'b')
            plot([x,x+sgn*prcnt/10.0],[y-0.2,y-0.2],'r')
            plot([x,x],[y,y],'.')

            for n in otherNbrs:
                plot([x, otherX], [y, otherY0-otherGsInd[n]])
            totalInt2Other += int2Other
            txt = "%d / %d" % (int2Other,  intAll)
            if ha=='right':
                txt = gSym(g) + " " + txt
            else:
                txt = txt + " " + gSym(g) 
            text(1.1*x,y,txt,horizontalalignment=ha,va="center")
            y-=1
        print(sId, totalInt2Other)
    xlim([-20,30]) 
    My = 1.2*max(len(gs1),len(gs2))/2
    ylim([-My,My]) 
    show() 

def testCount(genesFixed, genes, ppn):
    genesFixedS = {g for g in genesFixed if g in ppn.nodes} 
    if len(genesFixedS)==0:
        return
    gns = [x for x in genes if x in ppn.nodes and x not in genesFixedS]
    if len(gns)==0:
        return

    def scrF(ppn):
        return ppn.nBetweenInters(genesFixedS,gns)

    return scrF(ppn) 

if __name__ == "__test_shuffle_main__":
    realNds = {g:len(nbs) for g,nbs in list(ppn.nbrs.items())}
    assert len([1 for g1,nbs in list(ppn.nbrs.items()) if g1 in nbs]) == 0
    realE = old_div(sum([len(nbs) for nbs in list(ppn.nbrs.values())]),2)

    

    rnts = getRandNets(ppn,10)
    for rPpn in rnts:
        nds = {g:len(nbs) for g,nbs in list(rPpn.nbrs.items())}
        assert realNds == nds
        assert len([1 for g1,nbs in list(rPpn.nbrs.items()) if g1 in nbs]) == 0
        E = old_div(sum([len(nbs) for nbs in list(rPpn.nbrs.values())]),2)
        assert realE == E


if __name__ == "__draw_two_main__":
    ppn = PPINetwork('/home/iossifov/work/T115/PPI/hprd-ppimap.txt')
    fp = FunctionalProfiler()
    gSets,gWghts = fp.get_sets_and_weights(ppn.geneNS)   
    s1 = 'prb.LoF.Single'
    s2 = 'prb.Missense'
    figure()
    drawTwoSets(s1,s2,gSets,ppn)
    print(testCount(gSets.t2G[s1],gSets.t2G[s2],ppn))
    print(testCount(gSets.t2G[s2],gSets.t2G[s1],ppn))

    rnts = getRandNets(ppn,2)
    for rPpn in rnts:
        # raw_input("Press Enter to continue...")
        figure()
        drawTwoSets(s1,s2,gSets,rPpn)
        print(testCount(gSets.t2G[s1],gSets.t2G[s2],rPpn))
if __name__ == "__main__":
    fp = FunctionalProfiler()
    cmd = sys.argv[1]
    fn = sys.argv[2]

    if cmd=="ppn":
        ppn = PPINetwork(fn)
        shuffle = False
        if len(sys.argv)>3:
            shuffle=bool(sys.argv[3])
        fpRes = fp.profile_ppn(ppn,shuffle)
    elif cmd=='wn':
        wn = Matrix(fn)
        fpRes = fp.profile_wn(wn)
    elif cmd=='gts':
        gts = loadGeneTerm(fn)
        metric = 'tfidf'
        if len(sys.argv)>3:
            metric=sys.argv[3]
        fpRes = fp.profile_gts(gts,metric)
    elif cmd=='expression':
        SD = load_expression_data_bin(fn) 
        corrs = scipy.corrcoef(SD.expM)
        if len(np.nonzero(np.isnan(corrs))[0])>0:
            raise Exception("There are nan correlations")
        wn = Matrix(SD.genes['ID'],ConverttoNums(corrs))
        wn.numbers = np.abs(wn.numbers)
        wn.numbers[wn.numbers<0.0] = 0.0
        fpRes = fp.profile_wn(wn,ns=SD.atts['geneIdNS'])
    else:
        raise Exception('Unknown command: |' + cmd + "|")

    PF = open('fpRes.pckl','w')
    pklr = pickle.Pickler(PF)
    pklr.dump(fpRes) 
    PF.close() 

    fp.print_res_summary(sys.stdout,fpRes)
   
    # wn = Matrix('/data/safe/ecicek/Workspace6/Matrix/Sarah/Integrated/sarah.npz')
    # fpRes = fp.profile_wn(wn)
    # gts = giDB.getGeneTerms('disease',inNS=None)
    # gts = loadGeneTerm(daeDir + "/GeneToTermMapping/ProComp-map.txt")
    # gts = loadGeneTerm(daeDir + "/GeneToTermMapping/PPI-map.txt")
    # fpRes = fp.profile_gts(gts,metric='omni')

    # ppn = PPINetwork('/home/iossifov/work/T115/PPI/hprd-ppimap.txt')
    # ppn = PPINetwork('/home/iossifov/work/T115/PPI/intnet-ppimap.txt')
    # fpRes = fp.profile_ppn(ppn)
    # fp.print_res_summary(sys.stdout,fpRes)
