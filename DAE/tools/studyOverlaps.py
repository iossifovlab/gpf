#!/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from DAE import *
from collections import defaultdict


studies = [vDB.get_study(x) for x in vDB.get_study_names()]

pBuff = defaultdict(set)
sscCollections = sorted(set([pS.collection for pS in list(sfariDB.individual.values())]))
for pId,pS in list(sfariDB.individual.items()):
    pBuff[pId].add(pS.collection)

for stdy in studies:
    for f in list(stdy.families.values()):
        for p in f.memberInOrder:
            pBuff[p.personId].add(stdy.name)

allCollections = sscCollections + [s.name for s in studies]
print("\t".join(['pId','N'] + allCollections))
for pId in sorted(pBuff):
    ss = pBuff[pId]
    print("\t".join([pId,str(len(ss))] + ["1" if (c in ss) else "" for c in allCollections])) 
    
