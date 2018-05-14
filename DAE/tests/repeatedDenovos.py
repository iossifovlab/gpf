#!/bin/env python

from __future__ import print_function
from DAE import *

from collections import defaultdict
allDnvVs = list(vDB.get_denovo_variants('allWEAndTG'))

## the same family, the same gene
bf = defaultdict(list)

for v in allDnvVs: 
    for gs in set([ge['sym'] for ge in v.geneEffect]):
        bf[v.familyId + ":" + gs].append(v)


nb = 0
for fgs, lst in bf.items():
    if len(lst)==1:
        continue
    nb+=1
    print(nb, "###### ", fgs)
    for v in lst:
        print("|", v.study.name, "|", v.familyId, "|", v.location, "|", v.variant, "|", mat2Str(v.bestSt), "|", v.atts['effectType'])

## the same location+variant accross different families
vbf = defaultdict(lambda : defaultdict(list))
for v in allDnvVs: 
    vbf[v.location + ":" + v.variant][v.familyId].append(v)

for locVs, fams in vbf.items():
    if len(fams)==1:
        continue
    print("AAAAAAAAAAAA",  locVs, ",".join(fams))
 
    for fvs in fams.values(): 
        for v in fvs:
            print("|", v.study.name, "|", v.familyId, "|", v.location, "|", v.variant, "|", v.atts['effectType'], "|", v.atts['effectGene'])



