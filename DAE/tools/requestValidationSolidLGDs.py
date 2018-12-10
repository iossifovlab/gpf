#!/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from DAE import *
import getpass
import sys
from collections import defaultdict

# TODO get it from argv
studyName = 'wig683'
optionalAttsS = "counts,denovoScore,chi2APval,effectType,effectGene"
notInStudies = ""

if len(sys.argv)>1:
    studyName = sys.argv[1]

if len(sys.argv)>2:
    notInStudies = sys.argv[2]

if len(sys.argv)>3:
    optionalAttsS = sys.argv[3]


optionalAtts = []
if optionalAtts!="":
    optionalAtts = optionalAttsS.split(",")

maskedVariants = defaultdict(list) 
if notInStudies != "":
    for nisdy in (vDB.get_study(sn) for sn in notInStudies.split()):
        for v in nisdy.get_denovo_variants():
            k = ":".join((v.familyId,v.location,v.variant))
            maskedVariants[k].append(v)

validated = defaultdict(list) 
for vv in vDB.get_validation_variants():
    k = ":".join((vv.familyId,vv.location,vv.variant))
    validated[k].append(vv) 

nRequested = defaultdict(int)
print("\t".join("familyId location variant bestSt who why".split() + optionalAtts))
stdy = vDB.get_study(studyName)
for v in stdy.get_denovo_variants(effectTypes="LGDs"):
    k = ":".join((v.familyId,v.location,v.variant))
    if k in validated:
        continue
    if k in maskedVariants:
        continue
    print("\t".join([v.familyId,v.location,v.variant,mat2Str(v.bestSt),getpass.getuser(), "Test Solid LGDs"] + \
            [str(v.atts[a]) for a in optionalAtts]))
    nRequested[v.inChS] += 1
print("nRequested:", nRequested, file=sys.stderr)
