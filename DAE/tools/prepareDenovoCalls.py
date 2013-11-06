#!/bin/env python


from DAE import *
from subprocess import Popen
from subprocess import PIPE 
import sys
from collections import defaultdict
import re
from VariantsDB import str2Mat
from VariantsDB import parseGeneEffect
import VariantAnnotation
import sys
from numpy.lib.npyio import genfromtxt 

indelFN = '/data/safe/autism/pilot2/denovoCalls/objLinks/denovoIndels/1019/indel-CSHL-1019.txt'
subFN = '/data/safe/autism/pilot2/denovoCalls/objLinks/denovoSnvs/1019/snv-CSHL-1019.txt' 
quadReportFN = '/home/iossifov/work/T115/data-dev/study/wig1019/report_quad_20131006.txt'

if len(sys.argv) != 4:
    print >>sys.stderr , "need 3 arguments <quad report> <indel file> <sub file>"
    sys.exit(1)

quadReportFN = sys.argv[1]
indelFN = sys.argv[2]
subFN  = sys.argv[3]

# sys.exit(0)

prefix = 'denovo'
reannotateInput = False

def vKey(v):
    # what about the best state
    return ":".join([v.familyId,v.location,v.variant])

# load validation data
vRawData = defaultdict(list)
for v in vDB.get_validation_variants():
    vRawData[vKey(v)].append(v)
valStatusPriority = defaultdict(lambda:4,{ vst:(i+1) for i,vst in enumerate("valid invalid failed".split()) })
vData = {k:sorted(l,key=lambda v: valStatusPriority[v.valStatus])[0] for k,l in vRawData.items()}


def indelRecStrength(r):
    if r['passedIndelFilter']=='TRUE':
        return "strong"
    if r['passedSNVFilter']=='TRUE':
        return "weak"
    return "supper weak"

def subRecStrength(r):
    if r['SNVFilter']=='TRUE':
        return "strong"

    if float(r['pg.altPrcnt'])>0.5:
        return "supper weak"
    if float(r['noise.rate.prcnt'])>0.5:
        return "supper weak"
    if r['location'][0] == 'X':
        return "supper weak"
    bs = str2Mat(r['counts'],colSep=' ')
    if bs[1,0]>0 or bs[1,1]>0:
        return "supper weak"
    for c in xrange(2,bs.shape[1]):
        if bs[1,c]>=3:
            return "weak"
    return "supper weak"

strengthF = {"sub":subRecStrength, "indel":indelRecStrength}

fls = defaultdict(dict)
# open files
for vtype in "sub indel".split():
    for callSet in "listed strong clean strongToValidate weakToValidate".split():
        fls[vtype][callSet] = open('%s-%s-%s.txt' % (prefix, vtype, callSet), "w")

columnsToRemove = set("DEBUGEffectType DEBUGEffectGene DEBUGEffectDetails val.batchId val.counts val.status val.note val.parent".split())

LGDEffects = vDB.effectTypesSet('LGDs')
def isLGD(effectGene):
    for ge in parseGeneEffect(effectGene):
        if ge['eff'] in LGDEffects:
            return True
    return False

valVarsInLists = set()

stats = defaultdict(lambda : defaultdict(int))

standardValStatus = set("valid invalid failed".split())

def procDenovoFile(iFn,vtype):
    if reannotateInput:
        iF = Popen(["annotate_variants.py " + iFn + " | re_annotate_variants.py"], shell=True, stdout=PIPE).stdout
    else:
        iF = open(iFn)

    hdrRaw = iF.readline().strip().split("\t")
    hdr = list(hdrRaw)
    rmColInds = sorted([i for i,cn in enumerate(hdr) if cn in columnsToRemove],reverse=True)
    for i in rmColInds:
        del hdr[i]
    for oF in fls[vtype].values():
        oF.write("\t".join(hdr + "strength val.status val.counts val.batch val.parent val.note".split()) + "\n")
    for l in iF:
        # TODO: consider writing the comments to the listed file
        if l[0] == '#':
            continue
        cs = l.strip("\n\r").split("\t")
        for i in rmColInds:
            del cs[i]
        rec = dict(zip(hdr,cs))

        strn = strengthF[vtype](rec)
        cs += [strn] 

        vKey = ":".join([rec[x] for x in "familyId location variant".split()])
        valCols = [""]*5
        valStatus = ""
        if vKey in vData:
            vv = vData[vKey]
            valCols = [vv.valStatus,vv.valCountsS,vv.batchId,vv.valParent,vv.resultNote]
            valStatus = vv.valStatus 
            valVarsInLists.add(vKey)

        stats[vtype][strn]+=1
        if valStatus!="":
            stats[vtype][strn+"-valAtt"]+=1
            stValSt = valStatus
            if stValSt not in standardValStatus:
                stValSt = 'inconclusiv'
            stats[vtype][strn+"-valStat-"+stValSt]+=1

        cs += valCols    
        fsToWrite = [fls[vtype]['listed']]
        if strn=='strong':
            fsToWrite.append(fls[vtype]['strong'])
            if valStatus!='invalid':
                fsToWrite.append(fls[vtype]['clean'])

            # TODO: make sure that only LGDs are added to the request
            if valStatus=='' and isLGD(rec['effectGene']):
                fsToWrite.append(fls[vtype]['strongToValidate'])
                stats[vtype][strn+"-toValidate"]+=1
        else:
            if valStatus=='valid':
                fsToWrite.append(fls[vtype]['clean'])

            # TODO: make sure that only LGDs are added to the request
            if strn=='weak' and valStatus=='' and isLGD(rec['effectGene']):
                fsToWrite.append(fls[vtype]['weakToValidate'])
                stats[vtype][strn+"-toValidate"]+=1
        for oF in fsToWrite:
            oF.write("\t".join(cs) + "\n")
procDenovoFile(indelFN,"indel")
procDenovoFile(subFN,"sub")

# close files
[f.close() for dd in fls.values() for f in dd.values()]

for vtype,vtStats in stats.items():
    print "#############", vtype, "#############"
    print "\t".join("            ,N,valAtt,valid,invalid,failed,incon.,toValidate".split(','))
    for strn in "strong,weak,supper weak".split(","):
        print "\t".join(['%12s' % strn] + [str(vtStats[strn+x]) for x in ",-valAtt,-valStat-valid,-valStat-invalid,-valStat-failed,-valStat-inconclusiv,-toValidate".split(",")])

## load the ok families from the quad report
familyIdRE = re.compile('^auSSC(\d\d\d\d\d)') 
families = set() 
qrp = genfromtxt(quadReportFN,delimiter='\t',dtype=None,names=True, case_sensitive=True)
for qrpR in qrp:
    familyId = qrpR['quadquad_id']
    if familyIdRE.match(familyId):
        familyId = familyId[5:10]

    if qrpR['status'] == 'OK':
        families.add(familyId)

# otherValidatedF = open(prefix + 'otherValidated.txt', 'w')
GA = genomesDB.get_genome()
gmDB = genomesDB.get_gene_models()
# otherValidatedF = Popen(["annotate_variants.py - " + prefix + "-otherValidated.txt"], shell=True, stdin=PIPE).stdin
otherValidatedF = open(prefix + "-otherValidated.txt", "w")
otherValidatedF.write("\t".join(("familyId location variant strength val.batchId bestState val.status val.counts val.parent val.note inChild who why counts denovoScr chi2Pval effectType effectGene effectDetails".split()))+"\n")
        # oF.write("\t".join(hdr + "strength val.status val.counts, val.batch, val.fromParent, val.note".split()) + "\n")

otherStats = defaultdict(lambda : defaultdict(int))

for vKey,vv in vData.items():
    if vKey in valVarsInLists:
        continue            
    if vv.location.startswith('M:'):
        continue
    if vv.valStatus!="valid":
        continue
    if vv.familyId not in families:
        continue
    bs = vv.bestSt
    if bs[1,0]!=0 or bs[1,1]!=0:
        continue

    effects = VariantAnnotation.annotate_variant(gmDB, GA, loc=vv.location, var=vv.variant)
    desc = VariantAnnotation.effect_description(effects)
   
    vtype = 'indel'
    if 'sub' in vv.variant:
        vtype = 'sub'
    effType = "nonLGD"
    if isLGD(desc[1]):
        effType = "LGD"
    otherStats[vtype][effType]+=1
        

    addAtts = ['counts', 'denovoScore', 'chi2APval']
    otherValidatedF.write("\t".join(map(str,[vv.familyId,vv.location,vv.variant,"other",vv.batchId, vv.bestStS,vv.valStatus,vv.valCountsS, vv.valParent, vv.resultNote, vv.inChS,vv.who,vv.why]) + 
                    [str(vv.atts[aa]) if aa in vv.atts else "" for aa in addAtts] + list(desc)) + "\n")
otherValidatedF.close()

print "############# other #############"
print "\t".join(",LGD,nonLGD".split(","))
for vtype in "indel sub".split():
    print "\t".join([vtype,str(otherStats[vtype]["LGD"]),str(otherStats[vtype]['nonLGD'])])

