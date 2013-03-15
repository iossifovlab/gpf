#!/bin/env python

from DAE import *
from GeneTerms import loadGeneTerm
from VariantsDB import *
from phase import phase
from scipy.stats import binom
from scipy.stats import binom_test
import sys
from collections import defaultdict

class Counts:
    def __init__(self, study, 
                    geneSets=None, byGene=False, byFamilyGenderType=False, 
                    bySibGender=False, byParent=False, testsFilter=None ):
        self.byGene = byGene 
        self.geneSets = geneSets 
        self.study = study 
        self.byFamilyGenderType = byFamilyGenderType 
        self.bySibGender = bySibGender
        self.byParent = byParent 
        self.study = study 
        self.testsFilter = testsFilter 

        self.colNames = ['test']
        if self.byGene or self.geneSets:
            self.colNames.append('geneSet')
        if self.byFamilyGenderType or self.bySibGender:
            self.colNames.append('familyType')
        if self.byParent:
            self.colNames.append('fromParent')

        self.stats = defaultdict(lambda : defaultdict(int))

    def add(self, fid, gs, test, stat, par=None):
        if self.testsFilter and test not in self.testsFilter:
            return
        geneSets = ["all"]
        if self.byGene:
            geneSets.append("gene:" + gs)
        if self.geneSets:
            if gs in self.geneSets.g2T:
                geneSets.extend(("set:" + s for s in self.geneSets.g2T))

        famTps = ["all"]
        if self.byFamilyGenderType:
            famTps.append("full:" + "".join([self.study.families[fid].memberInOrder[i].gender for i in xrange(2,5)]))
        if self.bySibGender:
            famTps.append("sib:x" + self.study.families[fid].memberInOrder[3].gender)


        parGroups = ["both"]
        if self.byParent and par:
            parGroups.append(par)


        for gs in geneSets:
            for ft in famTps: 
                for pg in parGroups: 
                    keyA = [test]

                    if self.byGene or self.geneSets:
                        keyA.append(gs)
                    if self.byFamilyGenderType or self.bySibGender:
                        keyA.append(ft)
                    if self.byParent:
                        keyA.append(pg)
          
                    key = "\t".join(keyA) 
                    self.stats[key][stat]+=1

    def dump(self,out=None):
        toClose = False 
        if not out:
            f = sys.stdout
        elif isinstance(out,basestring):
            toClose = True 
            f = open(out)
        else: 
            f = out
        
        f.write("\t".join(self.colNames) + "\t" + "\t".join("neither prb sib both pVal".split()) + "\n");
        for tsKey, stat in self.stats.items():
            # two-sided: pval = binom_test(stat["10"], stat["10"]+stat["01"], p=0.5)
            pval = 1.0 - binom.cdf(stat["10"], stat["10"]+stat["01"], 0.5)

            cols = [tsKey]
            cols.extend((str(stat[k]) for k in "00 10 01 11".split()))
            cols.append(str(pval))

            f.write("\t".join(cols) + "\n")

        if toClose:
            close(f) 

class HomozygousTest:
    def __init__(self): 
        self.buff = defaultdict(lambda : defaultdict( list )) 

    def _phsType(self,vs):
        posFamilyPhs = phase([v.bestSt for v in vs])
        if len(posFamilyPhs)!=1:
            return "MultiBad"
        for pPhs in posFamilyPhs[0]:
            if len(set(pPhs[0,:])) > 1:
                return "MultiBoth" 
        return "OK"

    def addV(self,v):
        bs = v.bestSt
        if bs[0,1] + bs[1,1] == 1:
            return
        else: 
            if bs[1,0]==1 and bs[1,1]==1:
                for ge in v.requestedGeneEffects:
                    self.buff[v.familyId][ge['sym']].append(v)

    def done(self, counts):
        for fid,gss in self.buff.items():
            for gs,vs in gss.items(): 
                counts.add(fid, gs, "HomozygousGene", "TotalWithErr")
                for par,vs in pars.items():
                    if len(vs):
                        counts.add(fid, gs, "HomozygousGene", "Multi")
                        phsType = _phsType(vs)
                        if phsType != "OK":
                            counts.add(fid, gs, "HomozygousGene", phsType)
                            continue
                    st = vs[0].bestSt
                    a = 1 if bs[1,2]==2 else 0
                    s = 1 if bs[1,3]==2 else 0
                    counts.add(fid, gs, "HomozygousGene", "Total")
                    counts.add(fid, gs, "HomozygousGene", str(a)+str(s))

class DistTest:
    def __init__(self): 
        self.buff = defaultdict(lambda : defaultdict( lambda : defaultdict(list))) 
        self.buffX = defaultdict(lambda : defaultdict(list)) 

    def addV(self,v):
        bs = v.bestSt
        if bs[0,1] + bs[1,1] == 1:
            if bs[1,0]==1 and bs[1,1]==0:
                for ge in v.requestedGeneEffects:
                    self.buffX[v.familyId][ge['sym']].append(v)
        else: 
            if bs[1,0]==1 and bs[1,1]==0:
                for ge in v.requestedGeneEffects:
                    self.buff[v.familyId][ge['sym']]['mom'].append(v)
            if bs[1,0]==0 and bs[1,1]==1:
                for ge in v.requestedGeneEffects:
                    self.buff[v.familyId][ge['sym']]['dad'].append(v)

    def _phsTypeWithPhase(self,vs):
        posFamilyPhs = phase([v.bestSt for v in vs])
        if len(posFamilyPhs)!=1:
            return "MultiBad"
        for pPhs in posFamilyPhs[0]:
            if len(set(pPhs[0,:])) > 1:
                return "MultiBoth" 
        return "OK"


    def _phsTypeSimple(self,vs):
        transPatts = set()
        for v in vs:
            st = v.bestSt
            transPatts.add((st[1,2],  st[1,3]  ))
            transPatts.add((1-st[1,2],1-st[1,3]))
        if len(transPatts)!=2:
            return "MultiBad"
        if len({ v.bestSt[1,2] for v in vs })>1:
            return "MultiBoth"
        return "OK"

    def _phsType(self,vs):
        rSimple = self._phsTypeSimple(vs)
        # rPhs = self._phsTypeWithPhase(vs)
        rPhs = rSimple 
        if rSimple != rPhs:
            for v in vs:
                print v.bestSt
            raise Exception('AAAAAAAA: ' + rSimple + ", " + rPhs)
        return rSimple
                
    def done(self, counts):
        for fid,gss in self.buff.items():
            for gs,pars in gss.items(): 
                parBuf = [] 
                for par,vs in pars.items():
                    counts.add(fid, gs, "DistGene", "TotalWithErr", par)
                    if len(vs)>1:
                        counts.add(fid, gs, "DistGene", "Multi", par)
                        phsType = self._phsType(vs)
                        if phsType != "OK":
                            counts.add(fid, gs, "DistGene", phsType, par)
                            continue
                    st = vs[0].bestSt
                    a,s = st[1,2:4]
                    counts.add(fid, gs, "DistGene", "Total", par)
                    counts.add(fid, gs, "DistGene", str(a)+str(s), par)
                    parBuf.append((a,s))
                if len(parBuf) == 2:
                    a = 1 if all([x[0] for x in parBuf]) else 0
                    s = 1 if all([x[1] for x in parBuf]) else 0
                    counts.add(fid, gs, "CompoundHetGene", "Total")
                    counts.add(fid, gs, "CompoundHetGene", str(a)+str(s))
        for fid,gss in self.buffX.items():
            for gs,vs in gss.items(): 
                counts.add(fid, gs, "DistGeneX", "TotalWithErr")
                if len(vs)>1:
                    counts.add(fid, gs, "DistGeneX", "Multi", par)
                    phsType = self._phsType(vs)
                    if phsType != "OK":
                        counts.add(fid, gs, "DistGeneX", phsType, par)
                        continue
                st = vs[0].bestSt
                a,s = st[1,2:4]
                counts.add(fid, gs, "DistGeneX", "Total", par)
                counts.add(fid, gs, "DistGeneX", str(a)+str(s), par)
                parBuf.append((a,s))
                            
                
        
print "hi"

if __name__ == "__main__":
    setsFile = '/mnt/wigclust5/data/unsafe/autism/genomes/hg19/GeneSets'
    if len(sys.argv)>1:
        setsFile=sys.argv[1]
    
    geneTerms = loadGeneTerm(setsFile)
        
    study = vDB.get_study('wig683')

    cnts = Counts(study,bySibGender=True)
    distT = DistTest()

    # ultraRareOnly=False, effectTypes="LGDs"
    n = 0
    for v in study.get_transmitted_variants(ultraRareOnly=True, maxAltFreqPrcnt=1, effectTypes="LGDs"):
        distT.addV(v)
        n+=1
        # print n, v.inChS
    print >>sys.stderr, "number of variants:", n
    distT.done(cnts)
    cnts.dump()

