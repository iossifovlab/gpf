'''
Created on Jun 21, 2013

@author: leotta
'''
import itertools
import sys

from DAE import *
from VariantsDB import _safeVs

fatherRace = dict(zip(phDB.families,phDB.get_variable('focuv.race_parents')))
motherRace = dict(zip(phDB.families,phDB.get_variable('mocuv.race_parents')))

def augmentAVar(v):
    fmId = v.familyId
    parRaces = ",".join((m[fmId] if fmId in m else "NA" for m in [motherRace, fatherRace]))
    chProf = "".join((p.role + p.gender for p in v.memberInOrder[2:])) 
    v.atts["_par_races_"] = parRaces
    v.atts["_ch_prof_"] = chProf 
    return v

def loadTextColumn(colSpec):
    cn = 0
    sepC = "\t"
    header = 0
    cs = colSpec.split(',')
    fn = cs[0]
    if len(cs)>1:
        cn = int(cs[1])
    if len(cs)>2:
        sepC = cs[2]
    if len(cs)>3:
        header = int(cs[3])
    f = open(fn)
    if header == 1:
        f.readline()

    r = []
    for l in f:
        cs = l.strip().split(sepC)
        r.append(cs[cn])
    f.close()
    return r



# args is a dictionary with the following possible keys
# familiesFile
# geneSym
# geneSymFile
# geneId
# geneIdFile
# geneSet
# effectTypes
# denovoStudies
# transmittedStudy
# popFrequencyMax
# variantTypes
# inChild
# popMinParentsCalled
# popFrequencyMin
# 


def getVariantsInterface(args, response=None):
    
    requiredKeys = { 
                    'familiesFile':None,
                    'familiesList':None,
                    'geneSym':None,
                    'geneSymFile':None,
                    'geneId':None,
                    'geneIdFile':None,
                    'geneSet':None,
                    'effectTypes':None,
                    'denovoStudies':"None",
                    'transmittedStudy':"None",
                    'transmittedType':"None",
                    'popFrequencyMax':"1.0",
                    'variantTypes':None,
                    'inChild':None,
                    'popMinParentsCalled':"600",
                    'popFrequencyMin':"-1",
                    'regionS':None}

    for key,value in requiredKeys.items():
        if key not in args:
            args[key]=value

    families = None
    if args['familiesFile']:
        families = loadTextColumn(args['familiesFile'])

    if args['familiesList']:
        families = args['familiesList'].split(",")

    geneSyms = None

    if args['geneSym']:
        geneSyms = set(args['geneSym'].split(","))

    if args['geneSymFile']:
        geneSyms = set(loadTextColumn(args['geneSymFile']))

    geneIds = None
    if args['geneId']:
        geneIds = set(args['geneId'].split(","))
    
    if args['geneId']:
        geneIds = set(loadTextColumn(args['geneIdFile']))
    
    if geneIds:
        geneSyms = { giDB.genes[x].sym for x in geneIds if x in giDB.genes }
    
    if args['geneSet']:
        parts = args['geneSet'].split(":")
        if ":" in args['geneSet']:
            ci = args['geneSet'].index(":")
            collection = args['geneSet'][0:ci]
            setId = args['geneSet'][ci+1:] 
        else:
            collection = "main"
            setId = args['geneSet']
    
        # gts = giDB.getGeneTerms(collection)
        gts = get_gene_sets_symNS(collection,denovoStudies=args['denovoStudies'])
        geneSyms = set(gts.t2G[setId].keys())

    if args['variantTypes']:
        if args['variantTypes']=='All':
            args['variantTypes']=None

    if args['inChild']:
        if args['inChild']=='none' or args['inChild']=='All':
            args['inChild']=None

    # regionS
    # regionSFile
    
    effectTypes = None
    if args['effectTypes'] != "none":
        effectTypes = args['effectTypes']
    
    if args['effectTypes']:
        if args['effectTypes']=='All':            
            effectTypes="LGDs,CNVs,nonsynonymous,CNV-,CNV+,frame-shift,intron,no-frame-shift-new-stop,synonymous,nonsense,no-frame-shift,missense,3'UTR,5'UTR,splice-site"

    dvs = []
    if args['denovoStudies']!= "None" and args['denovoStudies']!= "none" and args['denovoStudies']!= "":
        try:
            dst = vDB.get_studies(args['denovoStudies'])
        except:
            print("The de novo study: " + args['denovoStudies'] + " DOES NOT EXIST! ...exiting!")
            raise
        dvs = vDB.get_denovo_variants(dst,
                        inChild=args['inChild'], variantTypes=args['variantTypes'], effectTypes=effectTypes,
                        familyIds=families,geneSyms=geneSyms,regionS=args['regionS'])
        #print "inChild=", args['inChild'], " variantTypes=", args['variantTypes'], ", effectTypes=", effectTypes, "familyIds=", families, ", geneSyms=", geneSyms, ", regionS=", args['regionS']
    
    ivs = []
    if args['transmittedStudy'] != "None" and args['transmittedStudy'] != "none" and args['transmittedStudy'] != "":
        popFreqMax = -1
        ultraRare = False 
        if args['popFrequencyMax']=="ultraRare":
            ultraRare = True
        else:
            popFreqMax = float(args['popFrequencyMax'])
        try:
            ist = vDB.get_study(args['transmittedStudy'])
        except:
            print("The transmitted study: " + args['transmittedStudy'] + " DOES NOT EXIST! ...exiting!")
            raise
        ivs = ist.get_transmitted_variants(variantTypes=args['variantTypes'], effectTypes=effectTypes,
                            inChild=args['inChild'],
                            minParentsCalled=float(args['popMinParentsCalled']),
                            minAltFreqPrcnt=float(args['popFrequencyMin']),
                            maxAltFreqPrcnt=popFreqMax,
                            ultraRareOnly=ultraRare,
                            familyIds=families,geneSyms=geneSyms,regionS=args['regionS'])

    additionalAtts = ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_', 'valstatus']

    if response==None:
        safeVs(itertools.imap(augmentAVar,itertools.chain(dvs,ivs)),'-', additionalAtts)
    else:
        _safeVs(response,itertools.imap(augmentAVar,itertools.chain(dvs,ivs)), additionalAtts)

