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

def printDt(dt,idCol,fn='-'):
    if fn=='-':
        f = sys.stdout
    else:
        f = open(fn,'w')

    cols =  sorted({c for row in dt.values() for c in row})
    f.write(idCol + "\t" + "\t".join([c[(c.index('.')+1):] for c in cols])+"\n")
    for id, row in sorted(dt.items()):
        f.write(id + "\t" + "\t".join([";".join(map(str,row[c]))   for c in cols]) + "\n")

    if fn!='-':
        f.close()

chldRoles = set(['prb','sib','twn'])
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
    rlsMp = { "mother":"mom", "father":"dad", "proband":"prb", "designated-sibling":"sib", "other-sibling":"sib", "proband-twin":"twn" }
    genderMap = {"female":"F", "male":"M"}

    roleOrdL = "mom,dad,prb,twn,sib".split(",")
    roleOrd  = {rl:i for i,rl in enumerate(roleOrdL)}

    fms = defaultdict(list) 
    fmColl  = defaultdict(set) 
    for indS in sfariDB.individual.values():
        # if indS.collection != 'ssc':
        #     continue
        class Person:
            pass
        p = Person()
        p.personId = indS.personId
        p.gender = genderMap[indS.sex]
        p.role = rlsMp[indS.role]
        fms[indS.familyId].append(p)
        fmColl[indS.familyId].add(indS.collection)

    for fid in fms:
        fms[fid] = sorted(fms[fid],key=lambda x: (roleOrd[x.role], x.personId))
        fmColl[fid] = ",".join(fmColl[fid])
    for fid,inds in fms.items():
        fam(fid,"0.sfri.chld",chldCode(inds))
        fam(fid,"0.sfri.collection",fmColl[fid])
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

def procWigStudy(stN, addSeqStatus=False, downloadHist=None):
    piAttN = ['mother', 'father', 'child1', 'child2']
    covAtt = '_target_covered_at_20_prcnt'

    st = vDB.get_study(stN)
    familyIdRE = re.compile('^\d\d\d\d\d$') 
        
    for fdsc in st.families.values() + st.badFamilies.values():
        if not familyIdRE.match(fdsc.familyId):
            continue
    
        fam(fdsc.familyId,"3.%s.chld" % stN, chldCode(fdsc.memberInOrder))
        if addSeqStatus:
            fam(fdsc.familyId,"3.%s.seqStatus" % stN, "processed") 
        if downloadHist:
            fam(fdsc.familyId,"3.%s.downloaded" % stN, downloadHist) 
        fam(fdsc.familyId,"3.%s.status" % stN, fdsc.atts['status'])
        fam(fdsc.familyId,"3.%s.jointCov" % stN, fdsc.atts['joint' + covAtt])
        for pi,p in enumerate(fdsc.memberInOrder):
            ind(p.personId,"02.gender",p.gender)
            ind(p.personId,"01.role",p.role)
            ind(p.personId,"3.%s.status" % stN, fdsc.atts['status'])
            ind(p.personId,"3.%s.jointCov" % stN, fdsc.atts['joint' + covAtt])
            ind(p.personId,"3.%s.indCov" % stN, fdsc.atts[piAttN[pi] + covAtt])

def mikeRAssignment(fn):
    f = open(fn)
    f.readline()
    for l in f:
        cs = l[:-1].split("\t")
        fid,ftype,coll,batch = cs
        if batch=="":
            continue
        fam(fid,"0.mikeRAssigned-ftype",ftype)
        fam(fid,"0.mikeRAssigned-coll",coll)
        fam(fid,"0.mikeRAssigned-batch",batch)

def lindaThirdAssignment(fn):
    f = open(fn)
    f.readline()
    for l in f:
        cs = l.strip().split(",")
        fid,coll,ftype,lab,assn,ancillary_notes,autoID = cs

        fam(fid,"0.sfri.collection",coll)

        # fam(fid,"0.lindaThird-coll",coll)
        # fam(fid,"0.lindaThird-ftype",ftype)
        # fam(fid,"0.lindaThird-ancilaryNotes",ancillary_notes)
        
def julieStatus(fn,stN):
    f = open(fn)
    f.readline()
    for l in f:
        cs = l[:-1].split("\t")
        fid = cs[0]
        status = cs[1]
        fam(fid,"3.%s.seqStatus" % stN,status)

def cshlUploadHistory(fn,stN):
    f = open(fn)
    # f.readline()
    for l in f:
        cs = l[:-1].split("\t")
        fid = cs[0]
        status = cs[1]
        fam(fid,"3.%s.uploadHist" % stN,status)

def yaleCurrentUpload(fn,stN):
    f = open(fn)
    # f.readline()
    for l in f:
        fid = l.strip()
        fam(fid,"3.%s.downloaded" % stN,"promised")

if __name__  == "__main__":
    # mikeRAssignment("MikeR-assignments.txt")
    procSfariSSC()
    procAssignment('EichlerAssigned')
    procAssignment('StateAssigned')
    procAssignment('WiglerAssigned')
    procWigStudy('wig1019',True)
    procWigStudy('wigState322',downloadHist="1 or 2")
    yaleCurrentUpload('/mnt/wigclust8/home/iossifov/work/sscExomeJointPaper/familyStatus/yale-201310-upload.txt','wigState322')
    # procWigStudy('wigEichler483',downloadHist="1, 2, or 3")
    procWigStudy('wigEichler515',downloadHist="1, 2, or 3")

    julieStatus('/mnt/wigclust8/home/iossifov/work/sscExomeJointPaper/familyStatus/familiesTillTheEnd-jr3-ii3-mr1.txt','wig1019')
    cshlUploadHistory('/mnt/wigclust8/home/iossifov/work/sscExomeJointPaper/familyStatus/ssc-upload-history-20131020.txt','wig1019')
    lindaThirdAssignment('/mnt/wigclust8/home/iossifov/work/sscExomeJointPaper/familyStatus/wigler_third_assignmnets.csv')

    printDt(famDt,"familyId",'famReport.txt')
    printDt(indDt,"personId",'indReport.txt')

