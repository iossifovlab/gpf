#!/bin/env python

from DAE import *
import sys

# TODO get it from argv
studyName = 'wig683'
stdy = vDB.get_study(studyName)
solidV = {}
for v in stdy.get_denovo_variants(callSet="noweak"):
    k = ":".join((v.familyId,v.location,v.variant))
    if k in solidV:
        raise Exception('lele')
    solidV[k] = v

print "\t".join(("familyId location variant batchId bestState valCounts inChild exCap.counts exCap.denovoScr exCap.chi2Pval".split()))

for vv in vDB.get_validation_variants():
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

    print "\t".join((vv.familyId,vv.location,vv.variant,vv.batchId, vv.bestStS,vv.valCountsS,vv.inChS,vv.atts['exCapcounts'],str(vv.atts['exCapdenovoScr']), str(vv.atts['exCapchi2Pval']))) 

print >>sys.stderr, "Can be annotated with: 'annotateVariants.sh -f aaa.txt -o aaa-ann.txt -x 2 -m 3'"
