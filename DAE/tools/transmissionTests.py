#!/bin/env python

from __future__ import print_function
from __future__ import division
from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object
from past.utils import old_div
from DAE import *
from GeneTerms import loadGeneTerm
from VariantsDB import *
from phase import phase
from scipy.stats import binom
from scipy.stats import binom_test
from scipy.stats import chi2

import numpy as np
import sys
from collections import defaultdict
import argparse

class Counts(object):
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

        autosomDistNull = np.array([0.23492706659, 0.249526546265, 0.250880396296, 0.264665990849])
        
        compoundNull = np.array([0.0,
                                 (autosomDistNull[1]+autosomDistNull[3])**2-autosomDistNull[3]**2,
                                 (autosomDistNull[2]+autosomDistNull[3])**2-autosomDistNull[3]**2,
                       autosomDistNull[3]**2])
        compoundNull[0] = 1.0 - compoundNull.sum()

        self.inhPattOrder = ['00', '10', '01', '11']
        self.inhPattPs = {"DistGene": autosomDistNull, "CompoundHitGene": compoundNull}


    def add(self, fid, geneSym, test, stat, par=None):
        if self.testsFilter and test not in self.testsFilter:
            return
        geneSets = ["all"]
        if self.byGene:
            geneSets.append("gene:" + geneSym)
        if self.geneSets:
            if geneSym in self.geneSets.g2T:
                geneSets.extend(("set:" + s for s in self.geneSets.g2T[geneSym]))
    

        famTps = ["all"]
        if self.byFamilyGenderType:
            famTps.append("full:" + "".join([self.study.families[fid].memberInOrder[i].gender for i in range(2,5)]))
        if self.bySibGender:
            famTps.append("sib:x" + self.study.families[fid].memberInOrder[3].gender)


        parGroups = ["either"]
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
        
        f.write("\t".join(self.colNames) + "\t" + "\t".join("neither prb sib both prbVsSibPVal patternPVal expCounts".split()) + "\n");
        for tsKey, stat in list(self.stats.items()):
            # two-sided: 
            prbVsSibPVal = binom_test(stat["10"], stat["10"]+stat["01"], p=0.5)

            pattPValS = ""
            expS = ""

            test = tsKey
            if "\t" in tsKey:
                test = tsKey[0:tsKey.index("\t")]

            if test in self.inhPattPs:
                ps = self.inhPattPs[test]
                O = np.array([stat[x] for x in self.inhPattOrder ])
                E = ps * O.sum()
                chiStat = sum(old_div((O-E)**2,E))
                pattPValS = str(1.0 - chi2.cdf(chiStat,3))
                expS = " ".join(['%.1f' % (x) for x in E])

            

            # one-sided ??
            # pval = 1.0 - binom.cdf(stat["10"], stat["10"]+stat["01"], 0.5)

            cols = [tsKey]
            cols.extend((str(stat[k]) for k in self.inhPattOrder ))

            cols.append(str(prbVsSibPVal))
            cols.append(pattPValS)
            cols.append(expS)

            f.write("\t".join(cols) + "\n")

        if toClose:
            close(f) 

class HomozygousTest(object):
    def __init__(self): 
        self.buff = defaultdict(lambda : defaultdict( list )) 

    def _phsType(self,vs):
        if len(vs)>5:
            return "Too many"
        posFamilyPhs = phase([v.bestSt for v in vs])
        if len(posFamilyPhs)!=1:
            return "MultiBad"
        for pPhs in posFamilyPhs[0]:
            if len(set(pPhs[0,:])) > 1:
                return "MultiBoth" 
        return "OK"

    def addV(self,v):
        if len(v.memberInOrder) != 4:
            return
        bs = v.bestSt
        if bs[0,1] + bs[1,1] == 1:
            return
        else: 
            if bs[1,0]==1 and bs[1,1]==1:
                for ge in v.requestedGeneEffects:
                    self.buff[v.familyId][ge['sym']].append(v)

    def done(self, counts):
        for fid,gss in list(self.buff.items()):
            for gs,vs in list(gss.items()): 
                counts.add(fid, gs, "HomozygousGene", "TotalWithErr")
                if len(vs)>5:
                    print("TOO MANY VARIANTS:", fid, gs, len(vs), file=sys.stderr)
                if len(vs):
                    counts.add(fid, gs, "HomozygousGene", "Multi")
                    phsType = self._phsType(vs)
                    if phsType != "OK":
                        counts.add(fid, gs, "HomozygousGene", phsType)
                        continue
                bs = vs[0].bestSt
                a = 1 if bs[1,2]==2 else 0
                s = 1 if bs[1,3]==2 else 0
                counts.add(fid, gs, "HomozygousGene", "Total")
                counts.add(fid, gs, "HomozygousGene", str(a)+str(s))

class DistTest(object):
    def __init__(self): 
        self.buff = defaultdict(lambda : defaultdict( lambda : defaultdict(list))) 
        self.buffX = defaultdict(lambda : defaultdict(list)) 

    def addV(self,v):
        if len(v.memberInOrder) != 4:
            return
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
                print(v.bestSt)
            raise Exception('AAAAAAAA: ' + rSimple + ", " + rPhs)
        return rSimple
                
    def done(self, counts):
        for fid,gss in list(self.buff.items()):
            for gs,pars in list(gss.items()): 
                parBuf = [] 
                for par,vs in list(pars.items()):
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
                    counts.add(fid, gs, "CompoundHitGene", "Total")
                    counts.add(fid, gs, "CompoundHitGene", str(a)+str(s))
        for fid,gss in list(self.buffX.items()):
            for gs,vs in list(gss.items()): 
                counts.add(fid, gs, "DistGeneX", "TotalWithErr")
                if len(vs)>1:
                    counts.add(fid, gs, "DistGeneX", "Multi", "mom")
                    phsType = self._phsType(vs)
                    if phsType != "OK":
                        counts.add(fid, gs, "DistGeneX", phsType, "mom")
                        continue
                st = vs[0].bestSt
                a,s = st[1,2:4]
                counts.add(fid, gs, "DistGeneX", "Total", "mom")
                counts.add(fid, gs, "DistGeneX", str(a)+str(s), "mom")
                # parBuf.append((a,s))
                            
                
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run transmission tests.")
    parser.add_argument('--denovoStudies', type=str, default="allWEAndTG", help='the denovo sutdies used to build the denovo gene set.' )
    parser.add_argument('--transmittedStudy', type=str, default="w1202s766e611", help='the transmitted study')
    parser.add_argument('--effectTypes', type=str, default="LGDs", help='effect types (i.e. LGDs,missense,synonymous). LGDs by default. ')
    parser.add_argument('--popFrequencyMax', type=str, default='1.0',
            help='maximum population frequency in percents. Can be 100 or -1 for no limit; ultraRare. 1.0 by default.')
    # parser.add_argument('--familiesFile', type=str, help='a file with a list of the families to report')
    parser.add_argument('--geneSets', default="main", type=str, help='gene sets (i.e. denovo, main, miRNA, ...)')
    args = parser.parse_args()

    print(args, file=sys.stderr)


    '''
    whiteFams = {f for f,mr,fr in zip(phDB.families,
                phDB.get_variable('focuv.race_parents'),
                phDB.get_variable('mocuv.race_parents')) if mr=='white' and fr=='white' }

    def getMeasure(mName):
        strD = dict(zip(phDB.families,phDB.get_variable(mName)))
        # fltD = {f:float(m) for f,m in strD.items() if m!=''}
        fltD = {}
        for f,m in strD.items():
            try:
                mf = float(m)
                fltD[f] = float(m)
            except:
                pass
        return fltD

    vIQ  = getMeasure('pcdv.ssc_diagnosis_verbal_iq')
    nvIQ = getMeasure('pcdv.ssc_diagnosis_nonverbal_iq')
    '''
    
 
    geneTerms = get_gene_sets_symNS(args.geneSets,denovoStudies=args.denovoStudies)
   
    ''' 
    # 
    fOutF = open('filterOutGenes.txt')
    fOutGns = {gn.strip() for gn in fOutF}
    fOutF.close()
    geneTerms.filterGenes(lambda gl: [g for g in gl if g not in fOutGns])
    '''

    ultraRareOnly = True
    maxAltFreqPrcnt = 1.0

    if args.popFrequencyMax != 'ultraRare':
        ultraRareOnly = False 
        maxAltFreqPrcnt = float(args.popFrequencyMax) 
        
        
    study = vDB.get_study(args.transmittedStudy)

    # familySubset = whiteFams & \
    #             {f for f,iq in nvIQ.items() if iq>90.0} & \
    #             {f.familyId for f in study.families.values() if f.memberInOrder[2].gender == 'M'}

    # familySubset = {f for f,iq in nvIQ.items() if iq>90.0}

    familySubset = None

    # print >>sys.stderr, "The size of the familySubset is", len(familySubset)

    cnts = Counts(study,geneSets=geneTerms,byParent=True, bySibGender=True)
    distT = DistTest()
    homozT = HomozygousTest()


    n = 0
    for v in study.get_transmitted_variants(ultraRareOnly=ultraRareOnly, maxAltFreqPrcnt=maxAltFreqPrcnt, effectTypes=args.effectTypes, familyIds=familySubset):
        distT.addV(v)
        homozT.addV(v)
        n+=1

    print("number of variants:", n, file=sys.stderr)
    distT.done(cnts)
    homozT.done(cnts)
    cnts.dump()

