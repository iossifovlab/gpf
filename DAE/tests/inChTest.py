#!/bin/env python

from DAE import *
import sys

exitCode=0

if len(vDB.studies)==0:
    exitCode=100

for st in vDB.studies.values():
    print st
    if not st.has_denovo:
        continue
    try:
        vs = [v for v in vDB.get_study(st.name).get_denovo_variants() if v.inChS!=v.atts['inChild'] ]
    except:
        print st.name, "FAIL"
	exitCode=-1 
        continue
         
    if vs:
        print st.name, len(vs)
        for v in vs:
            print "\t", v.familyId,v.inChS,v.atts['inChild']
	exitCode=-1

sys.exit(exitCode)
