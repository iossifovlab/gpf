#!/bin/env python

from DAE import *


for stN in vDB.get_study_names():
    st = vDB.get_study(stN)
    if not st.has_denovo:
        continue
    try:
        vs = [v for v in vDB.get_study(st.name).get_denovo_variants() if v.inChS!=v.atts['inChild'] ]
    except:
        print st.name, "FAIL" 
        continue
         
    if vs:
        print st.name, len(vs)
        for v in vs:
            print "\t", v.familyId,v.inChS,v.atts['inChild'] 
