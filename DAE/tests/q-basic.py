#!/bin/env python
from DAE import *
import sys

studyNamesS= 'wig683,DalyWE2012,EichlerWE2012,StateWE2012'
if len(sys.argv)>1:
    studyNamesS=sys.argv[1]

vIQ  = dict(zip(phDB.families,phDB.get_variable('pcdv.ssc_diagnosis_verbal_iq')))
nvIQ = dict(zip(phDB.families,phDB.get_variable('pcdv.ssc_diagnosis_nonverbal_iq')))
# ALSO CONSIDER pcdv.ssc_diagnosis_full_scale_iq

print "\t".join("study fid vIQ nvIQ LGD".split()) 

for studyName in studyNamesS.split(","): 
    study = vDB.get_study(studyName)
    allFams = study.families.keys()
    LGDVars = study.get_denovo_variants(effectTypes="LGDs",inChild="prb")
    LGDFams = set([v.familyId for v in LGDVars])

    for fid in allFams:
        print "\t".join((studyName, fid,
                    vIQ[fid] if fid in vIQ else "NA",
                    nvIQ[fid] if fid in nvIQ else "NA",
                    str(fid in LGDFams) ))
