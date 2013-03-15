#!/bin/env python

from DAE import *
import sys
from itertools import groupby
from collections import Counter 

# studyNamesS= 'wig683,DalyWE2012,EichlerWE2012,StateWE2012'
studyNamesS= 'wig683,DalyWE2012,EichlerWE2012,StateWE2012,wigState333,wigEichler374'
# studyNamesS= 'EichlerWE2012,StateWE2012,DalyWE2012'
# studyNamesS= 'wig683,wigState333,wigEichler374'
# studyNamesS= 'DalyWE2012'
stdyMap = { 'wig683': 'W' ,'DalyWE2012': 'D' ,'EichlerWE2012': 'E' ,'StateWE2012':'S', 'wigState333': 'S', 'wigEichler374': 'E' }

studies = [vDB.get_study(x) for x in studyNamesS.split(",")]

prbLGDs =  list(vDB.get_denovo_variants(studies,inChild='prb', effectTypes="LGDs"))

# studyNamesS= 'StateWE2012'
if len(sys.argv)>1:
    print sys.argv
    studyNamesS=sys.argv[1]



print "There are ", len(prbLGDs), "variants in probants"

gfiF = lambda x: x.familyId
fmSorted = sorted(prbLGDs,key=gfiF);
byFams = {k: list(g) for k, g in groupby(fmSorted, key=gfiF)}

for fmId, vs in byFams.items():
    if len(vs)==1:
       continue
    print "The proband of family ", fmId, "has", len(vs), "LGD variants"
    for v in vs:
        print "\t" + "\t".join((v.study.name, v.location, v.variant, v.atts['inChild'],  
                    "|".join([x['sym']+":"+x['eff'] for x in v.requestedGeneEffects]),
                            ))

# test for recurrence in the same probant
ccs = Counter([str(v.familyId)+":"+ge['sym']  for v in prbLGDs for ge in v.requestedGeneEffects ])
for fgs in ccs:
    if ccs[fgs]>1:
        print "WARNING: ", fgs, "is seen", ccs[fgs], "times"

gnSorted = sorted([[ge['sym'], v] for v in prbLGDs for ge in v.requestedGeneEffects ]) 
sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
sym2FN = { sym: len(set([v.familyId for v in vs])) for sym, vs in sym2Vars.items() } 

for g, FN in sorted(sym2FN.items(), key=lambda x: x[1]):
    print g + "\t" + str(FN),
    outSet = dict()
    for v in sym2Vars[g]:
        eff = ''
        for ge in v.requestedGeneEffects:
            if ge['sym'] == g:
                eff = ge['eff']
        if eff == '':
            raise Exception('breh')
        outSet[v.familyId] = "".join((stdyMap[v.study.name], eff[0], v.atts['inChild'][3])) 
    for o in outSet.values():
        print o,
    print

recCnt = Counter(sym2FN.values())
fs = set([f for s in studies for f in s.families])
print "The recurrence in", len(fs), "probants"
print "hits\tgeneNumber" 
for hn,cnt in sorted(recCnt.items(), key=lambda x: x[1]):
    print hn,"\t",cnt
