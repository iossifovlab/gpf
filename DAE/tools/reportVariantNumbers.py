#!/bin/env python

from DAE import *
import sys
from itertools import groupby
from collections import Counter 
from collections import defaultdict 
import scipy.stats as stats

studyNamesSA = ['wig683,wigState333,wigEichler374',
                'wigState333',
                'wigEichler374',
                'wig683',
                'DalyWE2012',
                'StateWE2012',
                'wigStateWE2012',
                'EichlerWE2012',
                'wigEichlerWE2012',
                'IossifovWE2012',
                'wig683,StateWE2012,wigStateWE2012,EichlerWE2012,wigEichlerWE2012,DalyWE2012',
                'IossifovWE2012,StateWE2012,EichlerWE2012,wigStateWE2012,wigEichlerWE2012,wig683']

if len(sys.argv)>1:
    studyNamesSA = sys.argv[1].split(";")

effTypesSA = [ 'LGDs', 'frame-shift', 'nonsense', 'splice-site', 'missense', 'synonymous', 'CNVs', 'CNV+', 'CNV-', 'noStart', 'noEnd', "5'UTR", "3'UTR", "3'UTR-intron", "5'UTR-intron", "intron" , "non-coding-intron", "non-coding"]
effTypesA = [ vDB.effectTypesSet(eftS) for eftS in effTypesSA ]
effTypeToInds = defaultdict(list)


children = ['prb', 'sib', 'prbM', 'prbF', 'sibM', 'sibF']

for i, eftSet in enumerate(effTypesA):
    for eft in eftSet:
        effTypeToInds[eft].append(i)
    
    

for studyNamesS in studyNamesSA:
    studies = vDB.get_studies(studyNamesS)

    print "STUDIES:", studyNamesS

    chldNHist = Counter()
    fmTpCnt = Counter()
    chldTpCnt = Counter()


    famBuff = defaultdict(dict)
    for sd in studies:
        for f in sd.families.values():
            for p in [f.memberInOrder[c] for c in xrange(2,len(f.memberInOrder))]:
                p._sTuDy = sd
                if p.personId in famBuff[f.familyId]:
                    pp = famBuff[f.familyId][p.personId]
                    if pp.role != p.role or pp.gender != p.gender:
                        # raise Exception("dddd")
                        print >>sys.stderr, "dddd:" + f.familyId
                else:
                    famBuff[f.familyId][p.personId] = p
                
    for fmd in famBuff.values():
        chldNHist[len(fmd)]+=1
   
        fmConf = "".join([fmd[pid].role + fmd[pid].gender for pid in sorted(fmd.keys(),key=lambda x: (fmd[x].role,x))])   
        fmTpCnt[fmConf]+=1

        for p in fmd.values():
            chldTpCnt[p.role + p.gender]+=1
            chldTpCnt[p.role]+=1

    print "FAMILIES:", len(famBuff) 
    print "\tBy number of children: " + ", ".join([str(nc) + ": " + str(chldNHist[nc]) for nc in sorted(chldNHist.keys())])
    print "\t" + str(chldTpCnt['prbM']), "male and", str(chldTpCnt['prbF']), "female probands."
    print "\t" + str(chldTpCnt['sibM']), "male and", str(chldTpCnt['sibF']), "female siblings."
    print "\t" +  ", ".join([x[0] + ": " + str(x[1]) for x in sorted(fmTpCnt.items(),key=lambda x: -x[1])])
    print "+++++++++++++++++++++++++++++++++++++++++++"

    cnts = defaultdict(lambda : defaultdict(int))


    def ratioStr(x,n):
        if n==0:
            return " NA  "
        return "%.3f" % (float(x)/n)

    def prcntStr(x,n):
        if n==0:
            return " NA  "
        return "%4.1f%%" % (100.0 * x / n)

    def bnmTst(xM,xF,NM,NF):
        if NM+NF==0:
            return " NA  "
        return "%.3f" % (stats.binom_test(xF, xF+xM, p=float(NF)/(NM+NF)))

    def filterVs(vs):
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

    print "effect      \t" + "\t".join([x.center(20) for x in children]) 
    print "------------------------------------------"

    for effT in effTypesSA: 
        print effT.ljust(12),
        for rl in children:
            vs  = list(vDB.get_denovo_variants(studies,inChild=rl, effectTypes=effT))
            vs = filterVs(vs)
            vCnt = len(vs)
            chCnt = len(set(v.familyId for v in vs))
            print "\t%3d,%s (%3d,%s)" %  (vCnt, ratioStr(vCnt, chldTpCnt[rl]), chCnt, prcntStr(chCnt, chldTpCnt[rl])),
            cnts[rl][effT] = vCnt 
        print
    print "------------------------------------------"


    for rtEffT in ['LGDs', 'missense', 'CNVs']:
        print rtEffT, "RATES:"
        print "\tProbands: all: %s, M: %s, F: %s (MvsF p-val: %s)" % ( ratioStr(cnts['prb'][rtEffT], chldTpCnt['prb']), 
                ratioStr(cnts['prbM'][rtEffT], chldTpCnt['prbM']), 
                ratioStr(cnts['prbF'][rtEffT], chldTpCnt['prbF']),
                bnmTst(cnts['prbM'][rtEffT], cnts['prbF'][rtEffT], chldTpCnt['prbM'], chldTpCnt['prbF']))
        print "\tSiblings: all: %s, M: %s, F: %s (MvsF p-val: %s)" % (ratioStr(cnts['sib'][rtEffT], chldTpCnt['sib']), 
                ratioStr(cnts['sibM'][rtEffT] , chldTpCnt['sibM']), 
                ratioStr(cnts['sibF'][rtEffT] , chldTpCnt['sibF']),
                bnmTst(cnts['sibM'][rtEffT], cnts['sibF'][rtEffT], chldTpCnt['sibM'], chldTpCnt['sibF']))
    print "\n"
    print "\n"


    





