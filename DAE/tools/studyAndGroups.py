#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from DAE import *

for stN in vDB.get_study_names():
    st = vDB.get_study(stN)
    print("study:", stN, st.name, st.has_denovo, st.has_transmitted, st.description)

for stGN in vDB.get_study_group_names():
    stG = vDB.get_study_group(stGN)
    print("studyGroup:", stGN, stG.name, stG.description, ";".join(stG.studyNames))

