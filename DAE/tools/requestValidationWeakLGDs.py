#!/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import range
from DAE import *
import getpass
import sys
from collections import defaultdict

# TODO get it from argv
studyName = 'wig683'
optionalAttsS = "who,why,counts,denovoScore,chi2APval,effectType,effectGene"
notInStudies = ""

if len(sys.argv)>1:
    studyName = sys.argv[1]

if len(sys.argv)>2:
    notInStudies = sys.argv[2]

if len(sys.argv)>3:
    optionalAttsS = sys.argv[3]

stdy = vDB.get_study(studyName)

optionalAtts = []
if optionalAtts!="":
    optionalAtts = optionalAttsS.split(",")

maskedVariants = defaultdict(list)
def keyF(v):
    return ":".join((v.familyId,v.location,v.variant))

if notInStudies != "":
    for nisdy in (vDB.get_study(sn) for sn in notInStudies.split()):
        for v in nisdy.get_denovo_variants():
            maskedVariants[keyF(v)].append(v)

for vv in vDB.get_validation_variants():
    maskedVariants[keyF(vv)].append(vv) 

for v in stdy.get_denovo_variants(effectTypes="LGDs"):
    maskedVariants[keyF(v)].append(v) 

nRequested = defaultdict(int)
reqVs = []
print("\t".join("familyId location variant bestSt".split() + optionalAtts))
for v in stdy.get_denovo_variants(effectTypes="LGDs",callSet="dirty"):
    if keyF(v) in maskedVariants:
        continue

    if v.variant.startswith('sub'):
        if v.atts['pgaltPrcnt']>0.5:
           continue
        if v.atts['noiserateprcnt']>0.5:
           continue
        # if v.atts['cleanCounts']==0:
        #    continue
        cnts = v.counts
        if cnts[1,0]>0 or cnts[1,1]>0:
            continue
        if all([cnts[1,c]<3 for c in range(2,cnts.shape[1])]):
            continue
        if v.location[0]=="X":
            continue
    else:
        continue
    v.atts['who'] = getpass.getuser()
    v.atts['why'] = "Test Weak SNV LGDs"
    print("\t".join([v.familyId,v.location,v.variant,mat2Str(v.bestSt)] + \
            [str(v.atts[a]) for a in optionalAtts]))
    nRequested[v.inChS] += 1
    reqVs.append(v)
print("nRequested:", nRequested, sum(nRequested.values()), file=sys.stderr)

'''
import tempfile
def viewVariants(vs,atts=[]):
    tf = tempfile.NamedTemporaryFile("w", delete=False)
    tf.write("\t".join("familyId location variant bestSt ".split()+atts)+"\n") 
    for v in vs:
        tf.write("\t".join(['"' + x + '"' for x in [v.familyId,v.location,v.variant,mat2Str(v.bestSt)] + [str(v.atts[a]) for a in atts]])+"\n")
    tfn = tf.name
    tf.close()
    print >>sys.stderr, "temp file name: " + tfn
    os.system("oocalc " + tfn)
    os.remove(tf.name)
'''
# viewVariants(reqVs,optionalAtts)
