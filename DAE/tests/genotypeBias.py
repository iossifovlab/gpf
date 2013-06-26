#!/bin/env python

from DAE import *
from collections import defaultdict
from collections import Counter 

# sd = vDB.get_study('wig683')
sd = vDB.get_study('w873e374s322')

dstDist = defaultdict(int) 
for v in sd.get_transmitted_variants(minAltFreqPrcnt=-1,maxAltFreqPrcnt=-1, effectTypes="synonymous", TMM_ALL=True):
    if len(v.memberInOrder) != 4:
        continue

    st = v.bestSt

    # filter out proper X
    if st[0,1] + st[1,1] == 1:
        continue

    # only one alternative in parents
    if st[1,0] + st[1,1] != 1:
        continue 

    dstDist[str(st[1,2])+str(st[1,3])]+=1
print dstDist
for k in sorted(dstDist): print k, float(dstDist[k])/sum(dstDist.values())

