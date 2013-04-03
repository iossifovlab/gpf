#!/bin/env python

from DAE import *
from collections import defaultdict
from collections import Counter 

sd = vDB.get_study('wig683')

dstDist = defaultdict(int) 
for v in sd.get_transmitted_variants(minAltFreqPrcnt=-1,maxAltFreqPrcnt=1, effectTypes="synonymous", TMM_ALL=True):
    st = v.bestSt
    if st[0,1] + st[1,1] == 1:
        continue
    if st[1,0] + st[1,1] != 1:
        continue 
    dstDist[str(st[1,2])+str(st[1,3])]+=1
print dstDist
for k in sorted(dstDist): print k, float(dstDist[k])/sum(dstDist.values())

# def get_denovo_variants(self, inChild=None, effectTypes=None, geneSyms=None, familyIds=None):
# inChild="prbM", effectTypes="LGDs"
print "There are", len(list(sd.get_denovo_variants(effectTypes="LGDs"))), "denovos in", len(sd.families), "families"
fmTpCnt = Counter()
for f in sd.families.values():
    fmTpCnt["".join([x.gender for x in f.memberInOrder[2:]])] += 1
print sorted(fmTpCnt.items(),key=lambda x: -x[1])
