#!/bin/env python

import re
from collections import defaultdict
from DAE import *

famDt = defaultdict(lambda : defaultdict(set))
def fam(fid,att,vl):
    famDt[fid][att].add(vl)
       
indDt = defaultdict(lambda : defaultdict(set))
def ind(pid,att,vl):
    indDt[pid][att].add(vl)

def printDt(dt,fn='-'):
    if fn=='-':
        f = sys.stdout
    else:
        f = open(fn,'w')

    cols =  sorted({c for row in dt.values() for c in row})
    f.write("id\t" + "\t".join(cols)+"\n")
    for id, row in sorted(dt.items()):
        f.write(id + "\t" + "\t".join([";".join(map(str,row[c]))   for c in cols]) + "\n")

    if fn!='-':
        f.close()

chldRoles = set(['prb','sib'])
sscPersonIdRE = re.compile('\d\d\d\d\d\.(..)')
def chldCode(membersInOrder):
    chldDsc = []
    for p in membersInOrder:
        if p.role not in chldRoles:
            continue
        chId = p.role
        if sscPersonIdRE.match(p.personId):
            chId = p.personId[6:] 
        chldDsc.append(chId+p.gender)
    return "".join(chldDsc)

def procSfariSSC():
    rlsMp = { "mother":"mom", "father":"dad", "proband":"prb", "designated-sibling":"sib", "other-sibling":"sib" }
    genderMap = {"female":"F", "male":"M"}

    roleOrdL = "mom,dad,prb,sib".split(",")
    roleOrd  = {rl:i for i,rl in enumerate(roleOrdL)}

    fms = defaultdict(list) 
    for indS in sfariDB.individual.values():
        if indS.collection != 'ssc':
            continue
        class Person:
            pass
        p = Person()
        p.personId = indS.personId
        p.gender = genderMap[indS.sex]
        p.role = rlsMp[indS.role]
        fms[indS.familyId].append(p)

    for fid in fms:
        fms[fid] = sorted(fms[fid],key=lambda x: (roleOrd[x.role], x.personId))
    for fid,inds in fms.items():
        fam(fid,"0.sfri.chld",chldCode(inds))
        for p in inds:
            ind(p.personId,"02.gender",p.gender)
            ind(p.personId,"01.role",p.role)

def procAssignment(stN):
    st = vDB.get_study(stN)
        
    for fdsc in st.families.values() + st.badFamilies.values():
        fam(fdsc.familyId,"1.%s.chld" % stN,chldCode(fdsc.memberInOrder))
        fam(fdsc.familyId,"0.assigned",stN[0])
        for pi,p in enumerate(fdsc.memberInOrder):
            ind(p.personId,"02.gender",p.gender)
            ind(p.personId,"01.role",p.role)
            ind(p.personId,"03.assigned",stN[0])

def procWigStudy(stN):
    piAttN = ['mother', 'father', 'child1', 'child2']
    covAtt = '_target_covered_at_20_prcnt'

    st = vDB.get_study(stN)
        
    for fdsc in st.families.values() + st.badFamilies.values():
        fam(fdsc.familyId,"3.%s.chld" % stN, chldCode(fdsc.memberInOrder))
        fam(fdsc.familyId,"3.%s.status" % stN, fdsc.atts['status'])
        fam(fdsc.familyId,"3.%s.jointCov" % stN, fdsc.atts['joint' + covAtt])
        for pi,p in enumerate(fdsc.memberInOrder):
            ind(p.personId,"02.gender",p.gender)
            ind(p.personId,"01.role",p.role)
            ind(p.personId,"3.%s.status" % stN, fdsc.atts['status'])
            ind(p.personId,"3.%s.jointCov" % stN, fdsc.atts['joint' + covAtt])
            ind(p.personId,"3.%s.indCov" % stN, fdsc.atts[piAttN[pi] + covAtt])

        

procSfariSSC()
procAssignment('EichlerAssigned')
procAssignment('StateAssigned')
procAssignment('WiglerAssigned')
procWigStudy('wig1019')
procWigStudy('wigState322')
procWigStudy('wigEichler483')

printDt(famDt,'famReport.txt')
printDt(indDt,'indReport.txt')

