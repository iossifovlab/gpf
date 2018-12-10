#!/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from builtins import map
from builtins import str
from DAE import *
import sys

# TODO get it from argv
studyName = 'wig1019'
stdy = vDB.get_study(studyName)
solidV = {}
for v in stdy.get_denovo_variants(callSet="noweak"):
    k = ":".join((v.familyId,v.location,v.variant))
    if k in solidV:
        raise Exception('lele')
    solidV[k] = v

print("\t".join(("familyId location variant batchId bestState val.status val.counts val.note inChild who why counts denovoScr chi2Pval".split())))

for vv in vDB.get_validation_variants():
    if vv.location.startswith('M:'):
        continue
    if vv.valStatus!="valid":
        continue
    if vv.familyId not in stdy.families:
        continue
    k = ":".join((vv.familyId,vv.location,vv.variant))
    if k in solidV:
        continue
    bs = vv.bestSt
    if bs[1,0]!=0 or bs[1,1]!=0:
        continue

    addAtts = ['counts', 'denovoScore', 'chi2APval']
    print("\t".join(list(map(str,[vv.familyId,vv.location,vv.variant,vv.batchId, vv.bestStS,vv.valStatus,vv.valCountsS, vv.resultNote, vv.inChS,vv.who,vv.why])) + 
                    [str(vv.atts[aa]) if aa in vv.atts else "" for aa in addAtts]))

print("Can be annotated with: 'annotateVariants.sh -f aaa.txt -o aaa-ann.txt -x 2 -m 3'", file=sys.stderr)
