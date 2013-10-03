#!/bin/env python

from DAE import *
from pylab import *
from itertools import groupby
from scipy.stats import ttest_ind
from scipy.stats import levene
import numpy as np
from collections import defaultdict
from collections import Counter 
from datetime import date


varData = phDB.get_variable('pumhx.medhx_fam_neurological.seizures_proband')


def varLen(v):
    lcS = v.location
    clnIn = lcS.index(':')
    dshIn = lcS.index('-')
    beg = int(lcS[clnIn+1:dshIn])
    end = int(lcS[dshIn+1:])
    return end-beg

def prbGender(fms):
    prbInds = [ind for ind,prsn in enumerate(fms.memberInOrder) if prsn.role=='prb']
    if len(prbInds)!=1:
        return '?'
    else:
        return fms.memberInOrder[prbInds[0]].gender

def fltVsOneVarPerGenePerChild(vs):
    ret = []
    seen = set()
    for v in vs:
        vKs = { v.familyId + "." + ge['sym'] for ge in v.requestedGeneEffects }
        if seen & vKs:
            continue
        ret.append(v) 
        seen |= vKs
    return ret

def fltVsInRecurrentGenes(vs):
    gnSorted = sorted([[ge['sym'], v] for v in vs for ge in v.requestedGeneEffects ]) 
    sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
    sym2FN = { sym: len(set([v.familyId for v in vs])) for sym, vs in sym2Vars.items() } 
    recGenes = { sym for sym,FN in sym2FN.items() if FN>1 }
    return [v for v in vs if { ge['sym'] for ge in v.requestedGeneEffects } & recGenes ]

def getRareInheritedDataSet(inLGDCandidates=True,maxAllelesInGene=20):
    std = vDB.get_study('wig683')

    sVars =       list(std.get_transmitted_summary_variants(minParentsCalled=300,  effectTypes="LGDs", maxAltFreqPrcnt=-1))
    allInhLGDs =  list(std.get_transmitted_variants        (minParentsCalled=300,  effectTypes="LGDs", maxAltFreqPrcnt=-1,inChild='prb'))

    lgdsParsLoci = defaultdict(int) 
    lgdsPars = defaultdict(int) 
    varFreq = defaultdict(int)
    varAltCnt = defaultdict(int)
    urVars = set()

    def keyF(v):
        return ":".join((v.location, v.variant)) 

    for sv in sVars:
        for g in sv.requestedGeneEffects:
            lgdsParsLoci[g['sym']]+=1
            lgdsPars[g['sym']]+=int(sv.atts['all.nAltAlls'])
        varFreq[keyF(sv)]=sv.altFreqPrcnt
        varAltCnt[keyF(sv)]=int(sv.atts['all.nAltAlls'])
        if sv.popType=="ultraRare":
            urVars.add(keyF(sv))

    dnvVars = list(vDB.get_denovo_variants(vDB.get_studies('allWE'),inChild='prb',effectTypes="LGDs"))

    gnSorted = sorted([[ge['sym'], v] for v in dnvVars for ge in v.requestedGeneEffects ]) 
    sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
    sym2Fms = { sym: set([v.familyId for v in vs]) for sym, vs in sym2Vars.items() } 

    # genesOfInterest = set(giDB.getGeneTerms('main').t2G['FMR1-targets'].keys())
    # genesOfInterest = set(giDB.getGeneTerms('domain').t2G['CHROMO'].keys())
    genesOfInterest = set(sym2Fms.keys())
    # genesOfInterest = set([g for g,fms in sym2Fms.items() if len(fms)>1])
    # genesOfInterest = set(sym2Fms.keys()) & set(giDB.getGeneTerms('main').t2G['FMR1-targets'].keys())



    allSeqFams = {f:prbGender(fms) for f,fms in std.families.items() }
    famsWithHit = defaultdict(int)
    for v in allInhLGDs:
        # if v.familyId not in whiteFams:
        #    continue
        hitsGoodGene = False
        for ge in v.requestedGeneEffects:
            if lgdsPars[ge['sym']]>maxAllelesInGene:
                continue
            if ge['sym'] not in genesOfInterest and inLGDCandidates:
                continue
            hitsGoodGene=True
            break
        if hitsGoodGene:
            famsWithHit[v.familyId]+=1
    return allSeqFams, famsWithHit


def getDataSet(studyNames,effectTypes,recurrentOnly=False,geneSym=None,geneSetDef=None,minVarLen=None):
    stds = vDB.get_studies(studyNames)

    geneSyms = None
    if geneSym:
        geneSyms = set([geneSym])
    if geneSetDef:
        gtId,tmId = geneSetDef.split(":")
        geneSyms = set(giDB.getGeneTerms(gtId).t2G[tmId].keys())

    vars = vDB.get_denovo_variants(stds,inChild='prb',effectTypes=effectTypes,geneSyms=geneSyms)

       
    vars = fltVsOneVarPerGenePerChild(vars)
    if minVarLen:
        vars = [v for v in vars if varLen(v)>minVarLen]
    if recurrentOnly:
        vars = fltVsInRecurrentGenes(vars)
 
    allSeqFams = {f:prbGender(fms) for st in stds for f,fms in st.families.items()}
    famsWithHit = Counter([v.familyId for v in vars])

    return allSeqFams,famsWithHit

sfri14Fams = {ind.familyId:ind.sex for ind in sfariDB.individual.values() if ind.role=='proband'}

dataSets = [] 

dataSets.append(["missensePublishedWEWithOurCalls",          getDataSet("allPublishedWEWithOurCalls",         "missense")])
dataSets.append(["synonymousPublishedWEWithOurCalls",        getDataSet("allPublishedWEWithOurCalls",         "synonymous")])
dataSets.append(["LGDsPublishedWEWithOurCalls",              getDataSet("allPublishedWEWithOurCalls",         "LGDs")])
dataSets.append(["recLGDsPublishedWEWithOurCalls",           getDataSet("allPublishedWEWithOurCalls",         "LGDs",recurrentOnly=True)])
dataSets.append(["LGDsInFMR1PPublishedWEWithOurCalls",       getDataSet("allPublishedWEWithOurCalls",         "LGDs",geneSetDef="main:FMR1-targets")])

dataSets.append(["missensePublishedWE",          getDataSet("allPublishedWE",         "missense")])
dataSets.append(["synonymousPublishedWE",        getDataSet("allPublishedWE",         "synonymous")])
dataSets.append(["LGDsPublishedWE",              getDataSet("allPublishedWE",         "LGDs")])
dataSets.append(["recLGDsPublishedWE",           getDataSet("allPublishedWE",         "LGDs",recurrentOnly=True)])
dataSets.append(["LGDsInFMR1PPublishedWE",       getDataSet("allPublishedWE",         "LGDs",geneSetDef="main:FMR1-targets")])

dataSets.append(["missenseWE",              getDataSet("allWE",               "missense")])
dataSets.append(["missenseSendWE",          getDataSet("allSendWE",           "missense")])
dataSets.append(["synonymousWE",            getDataSet("allWE",             "synonymous")])
dataSets.append(["synonymousSendWE",        getDataSet("allSendWE",         "synonymous")])
dataSets.append(["LGDsSendWE",              getDataSet("allSendWE",         "LGDs")])
dataSets.append(["recLGDsSendWE",           getDataSet("allSendWE",         "LGDs",recurrentOnly=True)])
dataSets.append(["LGDsInFMR1PSendWE",       getDataSet("allSendWE",         "LGDs",geneSetDef="main:FMR1-targets")])

dataSets.append(["CNV_LevyChris_large_dels",getDataSet("wig683,LevyCNV2011","CNV-",minVarLen=500000)])
dataSets.append(["CNV_LevyChris_large_dups",getDataSet("wig683,LevyCNV2011","CNV+",minVarLen=500000)])
dataSets.append(["CNV_LevyChris_dels",      getDataSet("wig683,LevyCNV2011","CNV-")])
dataSets.append(["CNV_LevyChris_dups",      getDataSet("wig683,LevyCNV2011","CNV+")])
dataSets.append(["CNV_LevyChris",           getDataSet("wig683,LevyCNV2011","CNVs")])
dataSets.append(["CNV_Levy_dels",           getDataSet("LevyCNV2011",       "CNV-")])
dataSets.append(["CNV_Levy_dups",           getDataSet("LevyCNV2011",       "CNV+")])
dataSets.append(["CNV_Levy_large_dels",     getDataSet("LevyCNV2011",       "CNV-",minVarLen=500000)])
dataSets.append(["CNV_Levy_large_dups",     getDataSet("LevyCNV2011",       "CNV+",minVarLen=500000)])
dataSets.append(["CNV_Chris_dels",          getDataSet("wig683",            "CNV-")])
dataSets.append(["CNV_Chris_dups",          getDataSet("wig683",            "CNV+")])
dataSets.append(["CNV_LevyChris_16p11.2",   getDataSet("wig683,LevyCNV2011","CNVs",geneSym='MAPK3')])
dataSets.append(["LGDsWEandTG",             getDataSet("allWEAndTG",        "LGDs")])
dataSets.append(["LGDsWE",                  getDataSet("allWE",             "LGDs")])
dataSets.append(["LGDsTG",                  getDataSet("EichlerTG2012",     "LGDs")])
dataSets.append(["LGDsInCHD8WEandTG",       getDataSet("allWEAndTG",        "LGDs",geneSym='CHD8')])
dataSets.append(["recLGDsWEandTG",          getDataSet("allWEAndTG",        "LGDs",recurrentOnly=True)])
dataSets.append(["recLGDsWE",               getDataSet("allWE",             "LGDs",recurrentOnly=True)])
dataSets.append(["LGDsInFMR1PWEandTG",      getDataSet("allWEAndTG",        "LGDs",geneSetDef="main:FMR1-targets")])
dataSets.append(["LGDsInFMR1PWE",           getDataSet("allWE",             "LGDs",geneSetDef="main:FMR1-targets")])

#dataSets.append(["rareInheritedLGDsInDenovoLGDcandidates", getRareInheritedDataSet(inLGDCandidates=True,maxAllelesInGene=20)])
#dataSets.append(["rareInheritedLGDs",                     getRareInheritedDataSet(inLGDCandidates=False,maxAllelesInGene=5)])


# dataSets.append(["LGDsWithCHROMOWEandTG",   getDataSet("allWEAndTG","LGDs",geneSetDef="domain:CHROMO")])
# dataSets.append(["LGDsWithCHROMOWE",        getDataSet("allWE","LGDs",geneSetDef="domain:CHROMO")])
def getCollectionCenter():
    f = open('ssc_age_at_assessment.csv')
    f.readline()  # header 
    famCenterS = defaultdict(set) 
    for l in f:
        cs = l.strip().split(',')
        fm,role = cs[0].split('.')
        center = cs[2]
        famCenterS[fm].add(center)


    ## assert
    if len([x for x in famCenterS.values() if len(x)>1])>0:
        raise Exception('aaa')

    famCenter = {f:s.pop() for f,s in famCenterS.items() }
    return famCenter


def getMeasure(mName):
    strD = dict(zip(phDB.families,phDB.get_variable(mName)))
    # fltD = {f:float(m) for f,m in strD.items() if m!=''}
    fltD = {}
    for f,m in strD.items():
        try:
            mf = float(m)
            # if mf>70:
            fltD[f] = float(m)
        except:
            pass 
    return fltD

def getMeasure2(mName):
    strD = dict(zip(phDB.families,phDB.get_variable(mName)))
    fltD = {}
    for f,m in strD.items():
        fltD[f] = m
    return fltD


# vIQ  = getMeasure('pcdv.ados_css')
vIQ  = getMeasure('pcdv.ssc_diagnosis_verbal_iq')
nvIQ = getMeasure('pcdv.ssc_diagnosis_nonverbal_iq') 
HC = getMeasure('pocuv.head_circumference') 
evlAge = getMeasure('phwhc.measure.eval_age_months') 
seizures_proband = getMeasure2('pumhx.medhx_fam_neurological.seizures_proband')


#collCenter = getCollectionCenter()

whiteFams = {f for f,mr,fr in zip(phDB.families,
                phDB.get_variable('focuv.race_parents'),
                phDB.get_variable('mocuv.race_parents')) if mr=='white' and fr=='white' }

tday = date.today()
mkF = open("phnGnt-%4d-%02d-%02d.txt" % (tday.year,tday.month,tday.day), "w")
mkF.write("\t".join("familyId,colletionCenter,probandGender,whiteParents,vIQ,nvIQ,hdCrcm,evalAgeInMonths,seizures".split(",") + [x[0] for x in dataSets]) + "\n")

for fmId,gender in sfri14Fams.items():
    mkF.write("\t".join([fmId,sfariDB.familyCenter[fmId],gender,"1" if fmId in whiteFams else "0"] +
                      [str(msr[fmId]) if fmId in msr else "NA" for msr in [vIQ,nvIQ,HC,evlAge]] ))
    
    if fmId in seizures_proband:
        if seizures_proband[fmId]=="true":
            value="1"
        elif seizures_proband[fmId]=="false":
            value="0"
        else:
            value="NA"
    else:
        value="NA"
        
    value="\t"+value
    
    mkF.write(value)
    
    for dtsN,(allFams,fmsWithHit) in dataSets:
        if fmId in allFams:
            if fmId in fmsWithHit:
                mkF.write("\t" + str(fmsWithHit[fmId]))
            else:
                mkF.write("\t0")
        else:
                mkF.write("\tNA")
    mkF.write("\n")
mkF.close()
