#!/bin/env python

from DAE import *
import sys
from itertools import groupby
from collections import Counter 
from collections import defaultdict 
import scipy.stats as stats

studyNamesSA = ['wig683,wigState333,wigEichler374',
                'wig683',
                'wigState333',
                'wigEichler374',
                'DalyWE2012']

if len(sys.argv)>1:
    studyNamesSA = sys.argv[1].split(";")

effTypesSA = [ 'LGDs', 'frame-shift', 'nonsense', 'splice-site', 'missense', 'synonymous' ]
effTypesA = [ vDB.effectTypesSet(eftS) for eftS in effTypesSA ]
effTypeToInds = defaultdict(list)


children = ['prb', 'sib', 'prbM', 'prbF', 'sibM', 'sibF']

for i, eftSet in enumerate(effTypesA):
    for eft in eftSet:
        effTypeToInds[eft].append(i)
    
    

for studyNamesS in studyNamesSA:
    studies = [vDB.get_study(x) for x in studyNamesS.split(",")]

    print "STUDIES:", studyNamesS

    trios = 0
    quads = 0
    fmTpCnt = Counter()
    prbCnt = Counter()
    sibCnt = Counter()
    for sd in studies:
        for f in sd.families.values():
            if len(f.memberInOrder)==3:
                trios+=1
            elif len(f.memberInOrder)==4:
                quads+=1
                sibCnt[f.memberInOrder[3].gender] += 1
            else:
                raise Exception('aaaa')

            fmTpCnt["".join([x.gender for x in f.memberInOrder[2:]])] += 1
            prbCnt[f.memberInOrder[2].gender] += 1
    print "FAMILIES:", str(quads+trios)
    print "\t" + str(quads), "quads; ", trios, "trios."
    print "\t" + str(prbCnt['M']), "male and", str(prbCnt['F']), "female probands."
    print "\t" + str(sibCnt['M']), "male and", str(sibCnt['F']), "female siblings."
    print "\t" +  " ".join([x[0] + ": " + str(x[1]) for x in sorted(fmTpCnt.items(),key=lambda x: -x[1])])
    print "+++++++++++++++++++++++++++++++++++++++++++"

    cnts = defaultdict(lambda : len(effTypesA)*[0])
    for rl in children:
        for v in vDB.get_denovo_variants(studies,inChild=rl):
            for i in effTypeToInds[v.atts['effectType']]:
                cnts[rl][i]+=1
    print "effect      \t" + "\t".join(children) 
    print "------------------------------------------"
    for i in xrange(len(effTypesA)):
        print effTypesSA[i].ljust(12) + "\t" + "\t".join([str(cnts[C][i]) for C in children])
    print "------------------------------------------"
    def ratioStr(x,n):
        if n==0:
            return " NA  "
        return "%.3f" % (float(x)/n)

    def bnmTst(xM,xF,NM,NF):
        if NM+NF==0:
            return " NA  "
        return "%.3f" % (stats.binom_test(xF, xF+xM, p=float(NF)/(NM+NF)))

    print "LGD RATES:"
    print "\tProbands: all: %s, M: %s, F: %s (MvsF p-val: %s)" % ( ratioStr(cnts['prb'][0], trios+quads), 
            ratioStr(cnts['prbM'][0], prbCnt['M']), 
            ratioStr(cnts['prbF'][0], prbCnt['F']),
            bnmTst(cnts['prbM'][0], cnts['prbF'][0], prbCnt['M'], prbCnt['F']))
    print "\tSiblings: all: %s, M: %s, F: %s (MvsF p-val: %s)" % (ratioStr(cnts['sib'][0], quads), 
            ratioStr(cnts['sibM'][0] , sibCnt['M']), 
            ratioStr(cnts['sibF'][0] , sibCnt['F']),
            bnmTst(cnts['sibM'][0], cnts['sibF'][0], sibCnt['M'], sibCnt['F']))
    print "\n"
    print "\n"


    





