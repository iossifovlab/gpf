#!/bin/env python

import ConfigParser
import os
import sys
from numpy.lib.npyio import genfromtxt 
import numpy as np
from pprint import pprint
from collections import defaultdict
from collections import Counter 
import copy
import gzip
import pysam 
import glob 
from os.path import dirname
from os.path import basename 
import tempfile
import re
from GeneTerms import GeneTerms
from itertools import groupby
from VariantAnnotation import get_effect_types_set

class DnvVariant:
    def __str__(self):
        return "DnvVariant\n\t" + "\n\t".join([str((x,getattr(self, x))) for x in dir(self) if x[0] != '_'])

class ParentVariant:
    def __str__(self):
        return "ParentVariant\n\t" + "\n\t".join([str((x,getattr(self, x))) for x in dir(self) if x[0] != '_'])

class Variant:
    def __init__(self,atts,familyIdAtt="familyId", locationAtt="location", 
                variantAtt="variant", bestStAtt="bestState", bestStColSep=-1,
                countsAtt="counts", effectGeneAtt="effectGene", altFreqPrcntAtt="all.altFreq"):
        self.atts = atts

        self.familyIdAtt = familyIdAtt
        self.locationAtt = locationAtt
        self.variantAtt = variantAtt
        self.bestStAtt = bestStAtt
        self.bestStColSep = bestStColSep
        self.countsAtt = countsAtt 
        self.effectGeneAtt = effectGeneAtt
        self.altFreqPrcntAtt = altFreqPrcntAtt

    @property
    def familyId(self):
        try:
            return self._familyId
        except AttributeError:
            pass
        self._familyId = str(self.atts[self.familyIdAtt])
        return self._familyId

    @property
    def studyName(self):
        return self.study.name

    @property
    def location(self):
        return self.atts[self.locationAtt]

    @property
    def variant(self):
        return self.atts[self.variantAtt]
            
    @property
    def bestStStr(self):
        return self.atts[self.bestStAtt]

    @property
    def bestSt(self):
        try:
            return self._bestSt
        except AttributeError:
            pass
        self._bestSt = str2Mat(self.atts[self.bestStAtt], colSep=self.bestStColSep)
        return self._bestSt

    @property
    def countsStr(self):
        return self.atts[self.countsAtt]

    @property
    def counts(self):
        try:
            return self._counts
        except AttributeError:
            pass
        self._counts = str2Mat(self.atts[self.countsAtt], colSep=" ")
        return self._counts

    @property
    def geneEffect(self):
        try:
            return self._geneEffect
        except AttributeError:
                self._geneEffect = parseGeneEffect(self.atts[self.effectGeneAtt])
        return self._geneEffect

    @property
    def requestedGeneEffects(self):
        try:
            return self._requestedGeneEffect
        except AttributeError:
                self._requestedGeneEffect = self.geneEffect
        return self._requestedGeneEffect

    @property
    def altFreqPrcnt(self):
        try:
            return self._altFreqPrcnt
        except AttributeError:
                self._altFreqPrcnt = 0.0
                if self.altFreqPrcntAtt in self.atts:
                    self._altFreqPrcnt = float(self.atts[self.altFreqPrcntAtt])
        return self._altFreqPrcnt

    @property
    def memberInOrder(self):
        try:
            return self._memberInOrder
        except AttributeError:
            self._memberInOrder = self.study.families[self.familyId].memberInOrder
        return self._memberInOrder
    
    @property
    def inChS(self):
        mbrs = self.memberInOrder
        # mbrs = elf.study.families[self.familyId].memberInOrder
        bs = self.bestSt
        childStr = ''
        for c in xrange(2,len(mbrs)):
            if isVariant(bs,c,self.location,mbrs[c].gender):
                childStr += (mbrs[c].role + mbrs[c].gender)
        return childStr

    @property
    def fromParentS(self):
        if self.popType == "denovo":
            if 'fromParent' in self.atts:
                return self.atts['fromParent']
            else:
                return ''
        parentStr = ''
        mbrs = self.memberInOrder
        bs = self.bestSt
        for c in xrange(2):
            if isVariant(bs,c,self.location,mbrs[c].gender):
                parentStr += mbrs[c].role
        return parentStr

    def get_normal_refCN(self,c):
        return normalRefCopyNumber(self.location,v.study.families[v.familyId].memberInOrder[c].gender)

    def is_variant_in_person(self,c):
        return isVariant(self.bestSt,c,self.location,self.memberInOrder[c].gender)
 
class Family:
    def __init__(self,atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {} 
    pass

class Person:
    def __init__(self,atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {} 

class StudyGroup:
    def __init__(self, vdb, name):
        self.vdb = vdb
        self.name = name
        self._configSection = 'studyGroup.' + name
       
        self.description = ""
        if self.vdb._config.has_option(self._configSection,'description'):
            self.description = self.vdb._config.get(self._configSection, 'description' )

        self.studyNames = self.vdb._config.get(self._configSection, 'studies' ).split(",")

    def get_attr(self,attName):
        if self.vdb._config.has_option(self._configSection,attName):
            return self.vdb._config.get(self._configSection,attName)

class Study:
    def __init__(self, vdb, name):
        self.vdb = vdb
        self.name = name
        self._configSection = 'study.' + name
        self._dnvData = {}
                
        self.has_denovo = self.vdb._config.has_option(self._configSection,'denovoCalls.files')
        self.has_transmitted = self.vdb._config.has_option(self._configSection,'transmittedVariants.indexFile')

        self.description = ""
        if self.vdb._config.has_option(self._configSection,'description'):
            self.description = self.vdb._config.get(self._configSection, 'description' )

        self._loaded = False
           
    def get_targeted_genes(self):
        if not self.vdb._config.has_option(self._configSection,"targetedGenes"):
            return
        tGsFN = self.vdb._config.get(self._configSection,"targetedGenes")
        tGsF = open(tGsFN) 
        tgsS = {l.strip() for l in tGsF}
        tGsF.close()
        return tgsS
         
    def get_attr(self,attName):
        if self.vdb._config.has_option(self._configSection,attName):
            return self.vdb._config.get(self._configSection,attName)
        
    def get_transmitted_summary_variants(self,minParentsCalled=600,maxAltFreqPrcnt=5.0,minAltFreqPrcnt=-1,variantTypes=None, effectTypes=None,ultraRareOnly=False, geneSyms=None, regionS=None):
        
        if not self._loaded:
            self._load_family_data()
                    
        transmittedVariantsFile = self.vdb._config.get(self._configSection, 'transmittedVariants.indexFile' ) + ".txt.bgz"
        print >> sys.stderr, "Loading trasmitted variants from ", transmittedVariantsFile 

        if isinstance(effectTypes,str):
            effectTypes = self.vdb.effectTypesSet(effectTypes)

        if isinstance(variantTypes,str):
            variantTypes = set(variantTypes.split(","))

        if regionS:
            f = gzip.open(transmittedVariantsFile)
            colNms = f.readline().strip().split("\t")
            f.close()
            tbf = pysam.Tabixfile(transmittedVariantsFile)
            f = tbf.fetch(regionS)
        else:
            f = gzip.open(transmittedVariantsFile)
            colNms = f.readline().strip().split("\t")

        for l in f:
            if l[0] == '#':
                continue
            vls = l.strip().split("\t")
            if len(colNms) != len(vls):
                raise Exception("Incorrect transmitted variants file: " + transmittedVariantsFile)
            mainAtts = dict(zip(colNms,vls))

            mainAtts["location"] = mainAtts["chr"] + ":" + mainAtts["position"]

            if minParentsCalled != -1:
                parsCalled = int(mainAtts['all.nParCalled'])
                if parsCalled <= minParentsCalled:
                    continue

            if maxAltFreqPrcnt != -1 or minAltFreqPrcnt != -1:
                altPrcnt = float(mainAtts['all.altFreq'])
                if maxAltFreqPrcnt != -1 and altPrcnt > maxAltFreqPrcnt:
                    continue
                if minAltFreqPrcnt != -1 and altPrcnt < minAltFreqPrcnt:
                    continue

            ultraRare = int(mainAtts['all.nAltAlls'])==1
            if ultraRareOnly and not ultraRare:
                continue

            geneEffect = None
            if effectTypes or geneSyms:
                geneEffect = parseGeneEffect(mainAtts['effectGene'])
                requestedGeneEffects = filter_gene_effect(geneEffect, effectTypes, geneSyms)
                if not requestedGeneEffects:
                    continue
            v = Variant(mainAtts)
            v.study = self

            if geneEffect != None:
                v._geneEffect = geneEffect
                v._requestedGeneEffect = requestedGeneEffects
            if ultraRare:
                v.popType="ultraRare"
            else:
                # rethink
                v.popType="common" 

            if variantTypes and v.variant[0:3] not in variantTypes:
                continue

            yield v

        if regionS:
            tbf.close()
        else:
            f.close()


    def get_transmitted_variants(self, inChild=None, minParentsCalled=600,maxAltFreqPrcnt=5.0,minAltFreqPrcnt=-1,variantTypes=None,effectTypes=None,ultraRareOnly=False, geneSyms=None, familyIds=None, regionS=None, TMM_ALL=False):
        
        if not self._loaded:
            self._load_family_data()
                    
        transmittedVariantsTOOMANYFile = self.vdb._config.get(self._configSection, 'transmittedVariants.indexFile' ) + "-TOOMANY.txt.bgz"

        if TMM_ALL:
            tbf = gzip.open(transmittedVariantsTOOMANYFile)
        else:
            tbf = pysam.Tabixfile(transmittedVariantsTOOMANYFile)

        for vs in self.get_transmitted_summary_variants(minParentsCalled,maxAltFreqPrcnt,minAltFreqPrcnt,variantTypes,effectTypes,ultraRareOnly, geneSyms, regionS):
            fmsData = vs.atts['familyData']
            if not fmsData:
                continue 
            if fmsData == "TOOMANY":
                chr = vs.atts['chr']
                pos = vs.atts['position']
                var = vs.atts['variant']
                if TMM_ALL:
                    for l in tbf:
                        chrL,posL,varL,fdL = l.strip().split("\t")
                        if chr==chr and pos==posL and var==varL:
                            fmsData = fdL
                            break
                    if fmsData == "TOOMANY":
                        raise Exception('TOOMANY mismatch TMM_ALL')
                else:
                    flns = []
                    posI = int(pos)
                    for l in tbf.fetch(chr, posI-1, posI):
                        chrL,posL,varL,fdL = l.strip().split("\t")
                    
                        if chr==chr and pos==posL and var==varL:
                            flns.append(fdL)
                    if len(flns)!=1:
                        raise Exception('TOOMANY mismatch')
                    fmsData = flns[0]

            for fmData in fmsData.split(";"):
                cs = fmData.split(":") 
                if len(cs) != 3:
                    raise Exception("Wrong family data format: " + fmData)
                familyId, bestStateS, cntsS = cs 
                if familyIds and familyId not in familyIds:
                    continue
                v = copy.copy(vs)
                v.atts = { kk: vv for kk,vv in vs.atts.items() }
                v.atts['familyId'] = familyId
                v.atts['bestState'] = bestStateS
                v.atts['counts'] = cntsS

                if inChild and inChild not in v.inChS:
                    continue
                yield v
        tbf.close()

    def get_denovo_variants(self, inChild=None, variantTypes=None, effectTypes=None, geneSyms=None, familyIds=None, regionS=None, callSet=None):

        if not self._loaded:
            self._load_family_data()
            
        if isinstance(effectTypes,str):
            effectTypes = self.vdb.effectTypesSet(effectTypes)

        if isinstance(variantTypes,str):
            variantTypes = set(variantTypes.split(","))

        if regionS:
            smcP = regionS.find(":")
            dsP = regionS.find("-")
            chr = regionS[0:smcP]
            beg = int(regionS[smcP+1:dsP])
            end = int(regionS[dsP+1:])

        dnvData = self._load_dnv_data(callSet)
        for v in dnvData:
            if familyIds and v.familyId not in familyIds:
                continue
            if inChild and inChild not in v.inChS:
                continue
            if variantTypes and v.variant[0:3] not in variantTypes:
                continue
            if regionS:
                smcP = v.location.find(":")
                vChr = v.location[0:smcP]
                vPos = int(v.location[smcP+1:]) 
                if vChr!=chr:
                    continue
                if vPos<beg or vPos>end:
                    continue
            if effectTypes or geneSyms:
                requestedGeneEffects = filter_gene_effect(v.geneEffect, effectTypes, geneSyms)
                if not requestedGeneEffects:
                    continue
                vc = copy.copy(v)
                vc._requestedGeneEffect = requestedGeneEffects
                yield vc 
            else:
                yield v
                

    def _load_dnv_data(self, callSetP):
        callSet =  "default"
        propName = "denovoCalls.files"

        if callSetP:
            callSet = callSetP
            propName = "denovoCalls." + callSet + ".files"
        
        if callSet in self._dnvData:
            return self._dnvData[callSet]
 
        flsS = self.vdb._config.get(self._configSection, propName)
        varList = []
        for fl in flsS.split('\n'):
            print >> sys.stderr, "Loading file", fl, "for collection ", self.name 
            dt = genfromtxt(fl,delimiter='\t',dtype=None,names=True,
                            case_sensitive=True)
            if len(dt.shape)==0:
                dt = dt.reshape(1)
            hasCenter = 'center' in dt.dtype.names;
            for vr in dt:
                atts = { x: vr[x] for x in dt.dtype.names }
                if not hasCenter:
                    atts['center'] = "CSHL"

                v = Variant(atts,bestStColSep=" ")
                v.popType = "denovo"
                v.study = self
                varList.append(v)

        self._dnvData[callSet] = varList
        return varList


    def _load_family_data(self):
        fdFile = self.vdb._config.get(self._configSection, "familyInfo.file" )
        fdFormat = self.vdb._config.get(self._configSection, "familyInfo.fileFormat" )
   
        fmMethod = { 
            "quadReportSSC": self._load_family_data_from_quad_report,
            "simple": self._load_family_data_from_simple,
            "StateWE2012-data1-format": self._load_family_data_from_StateWE2012_data1,        
            "EichlerWE2012-SupTab1-format": self._load_family_data_from_EichlerWE2012_SupTab1,
            "DalyWE2012-SD-Trios": self._load_family_data_from_DalyWE2012_SD_Trios,
            "SSCTrios-format": self._load_family_data_SSCTrios,
            "SSCFams-format": self._load_family_data_SSCFams
        }
    

        if fdFormat not in fmMethod:
            raise Exception("Unknown Family Fdef __init__(self,vdb,name):ile Format: " + fdFormat)

        self.families, self.badFamilies = fmMethod[fdFormat](fdFile)
        self._loaded = True
        
    def _load_family_data_SSCFams(self, reportF):
        rf = open(reportF)
        families = {l.strip():Family() for l in rf}
        for f in families.values():    
            f.memberInOrder = []

        rlsMp = { "mother":"mom", "father":"dad", "proband":"prb", "designated-sibling":"sib", "other-sibling":"sib" }
        genderMap = {"female":"F", "male":"M"}

        for indS in self.vdb._sfariDB.individual.values():
            if indS.familyId not in families:
                continue
            p = Person()
            p.personId = indS.personId
            p.gender = genderMap[indS.sex]
            p.role = rlsMp[indS.role]
            families[indS.familyId].memberInOrder.append(p)
        return families,{}


    def _load_family_data_SSCTrios(self, reportF):
        buff = defaultdict(dict) 
        for indId,indS in self.vdb._sfariDB.individual.items():
            if indS.collection != "ssc":
                continue
            buff[indS.familyId][indS.role] = indS

        rlsMp = zip("mother,father,proband".split(','),"mom,dad,prb".split(','))
        genderMap = {"female":"F", "male":"M"}


        families = {}
        for fid,rls in buff.items():
            if "mother" not in rls or "father" not in rls or "proband" not in rls:
                continue
            f = Family()
            f.familyId = fid
            f.memberInOrder = []
            
            for srl,irl in rlsMp:
                p = Person()
                p.personId = rls[srl].personId
                p.gender = genderMap[rls[srl].sex]
                p.role = irl
                f.memberInOrder.append(p)
            families[f.familyId] = f 
        return families,{}


    def _load_family_data_from_simple(self,reportF):
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments="asdgasdgasdga")
        families = defaultdict(Family)
        for dtR in dt:
            fmId = str(dtR['familyId'])
            families[fmId].familyId = fmId
            atts = { x: dtR[x] for x in dt.dtype.names }
            p = Person(atts)
            p.personId = atts['personId']
            p.gender = atts['gender']
            p.role = atts['role']
            try:
                families[fmId].memberInOrder.append(p)
            except AttributeError:
                families[fmId].memberInOrder = [p]
        return families,{}
            

    
    def _load_family_data_from_DalyWE2012_SD_Trios(self,reportF):
        families = {}

        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments="asdgasdgasdga")

        genderDecoding = { "female":"F", "male":"M"}

        for dtR in dt:
            atts = { x: dtR[x] for x in dt.dtype.names }
            prb = Person(atts)
            prb.gender = genderDecoding[dtR["Gender"]]
            prb.role = "prb"
            prb.personId = dtR["Child_ID"]

            fid = prb.personId

            mom = Person()
            mom.personId = fid + ".mo"
            mom.role = 'mom'
            mom.gender = 'F'

            dad = Person()
            dad.personId = fid + ".fa"
            dad.role = 'dad'
            dad.gender = 'M'

            f = Family()
            f.familyId = fid
            f.memberInOrder = [mom, dad, prb]

            families[fid] = f
        return families,{}

    def _load_family_data_from_EichlerWE2012_SupTab1(self,reportF):
        famBuff = defaultdict(dict)
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments="asdgasdgasdga")

        genderDecoding = { "female":"F", "male":"M"}
        roleDecoding = { "SSC189":"prb", "SSC189_Sib":"sib", "Pilot_Pro":"prb", "Pilot_Sib":"sib" }

        for dtR in dt:
            atts = { x: dtR[x] for x in dt.dtype.names }
            p = Person(atts)
            p.gender = genderDecoding[dtR["sex"]]
            p.role = roleDecoding[dtR["type"]]
            p.personId = dtR["child"] 

            pid = p.personId
            fid = pid[0:pid.find('.')]

            famBuff[fid][p.role] = p

        families = {}
        for fid,pDct in famBuff.items():
            f = Family()
            f.familyId = fid

            mom = Person()
            mom.personId = fid + ".mo"
            mom.role = 'mom'
            mom.gender = 'F'

            dad = Person()
            dad.personId = fid + ".fa"
            dad.role = 'dad'
            dad.gender = 'M'

            # print fid, pDct.keys()
            if len(pDct) == 1:
                f.memberInOrder = [mom, dad, pDct['prb']]
            elif len(pDct) == 2:
                f.memberInOrder = [mom, dad, pDct['prb'], pDct['sib']]
            else:
                raise Exception("Weird family: " + fid + " with " + str(len(pDct)) + " memmbers")

            families[fid] = f

        return families,{}


    def _load_family_data_from_StateWE2012_data1(self,reportF):
        famBuff = defaultdict(dict) 
        badFamBuff = defaultdict(dict) 
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True, comments="asdgasdgasdga")

        genderDecoding = { "Male":"M", "Female":"F" }
        roleDecoding = { "Mother":"mom", "Father":"dad", "Affected_proband":"prb", "Unaffected_Sibling":"sib" }

        for dtR in dt:
            atts = { x: dtR[x] for x in dt.dtype.names }
            p = Person(atts)
            p.gender = genderDecoding[dtR["Gender"]]
            p.role = roleDecoding[dtR["Role"]]
            p.personId = dtR["Sample"] 

            if dtR['Sample_PassFail'] == 'Fail' or dtR['Family_PassFail'] == 'Fail':
                badFamBuff[str(dtR["Family"])][p.role] = p
            else:
                famBuff[str(dtR["Family"])][p.role] = p


        families = {}
        for fid,pDct in famBuff.items():
            f = Family()
            f.familyId = fid

            # print fid, pDct.keys()
            if len(pDct) == 3:
                f.memberInOrder = [pDct['mom'], pDct['dad'], pDct['prb']]
            elif len(pDct) == 4:
                f.memberInOrder = [pDct['mom'], pDct['dad'], pDct['prb'],pDct['sib']]
            else:
                raise Exception("Weird family: " + fid + " with " + str(len(pDct)) + " memmbers")

            families[fid] = f

        badFamilies = {}
        for fid,pDct in badFamBuff.items():
            f = Family()
            f.familyId = fid

            f.memberInOrder = pDct.values()

            badFamilies[fid] = f

        return families,badFamilies
       

    def _load_family_data_from_quad_report(self,reportF):
        familyIdRE = re.compile('^auSSC(\d\d\d\d\d)') 
        families = {}
        badFamilies = {}
        qrp = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True)
        for qrpR in qrp:
            f = Family()
            f.familyId = qrpR['quadquad_id']
            if familyIdRE.match(f.familyId):
                f.familyId = f.familyId[5:10]

            f.atts = { x:qrpR[x] for x in qrp.dtype.names }

            def piF(pi):
                sfariDB = self.vdb._sfariDB
                if not sfariDB:
                    return pi
                if pi not in sfariDB.sampleNumber2PersonId:
                    return pi
                return sfariDB.sampleNumber2PersonId[pi]

            mom = Person()
            mom.personId = piF(qrpR['mothersample_id'])
            mom.role = 'mom'
            mom.gender = 'F'

            dad = Person()
            dad.personId = piF(qrpR['fathersample_id'])
            dad.role = 'dad'
            dad.gender = 'M'

            prb = Person()
            prb.personId = piF(qrpR['child1sample_id'])
            prb.role = 'prb'
            prb.gender = qrpR['child1gender']

            
            f.memberInOrder = [mom, dad, prb]
           
            if qrpR['child2sample_id']: 
                sib= Person()
                sib.personId = piF(qrpR['child2sample_id'])
                sib.role = 'sib'
                sib.gender = qrpR['child2gender']
                f.memberInOrder.append(sib)
            if qrpR['status'] == 'OK':
                families[f.familyId] = f
            else:
                badFamilies[f.familyId] = f

        return families,badFamilies

class VariantsDB:
    def __init__(self, daeDir, confFile=None, sfariDB=None, giDB=None):
        
        self._sfariDB = sfariDB
        self._giDB = giDB
        if not confFile:
            confFile = daeDir + "/variantDB.conf"
            
        self._config = ConfigParser.SafeConfigParser({'wd':daeDir})
        self._config.optionxform = lambda x: x
        
        self._config.read(confFile)
        
        self._studies = {}
        for secName in self._config.sections():
            if secName.startswith('study.'):
                studyName = secName[6:]
                self._studies[studyName] = Study(self,studyName)

        self._studyGroups = {}
        for secName in self._config.sections():
            if secName.startswith('studyGroup.'):
                gName = secName[11:]
                self._studyGroups[gName] = StudyGroup(self,gName)

                for stN in self._studyGroups[gName].studyNames:
                    if stN not in self._studies:
                        raise Exception("The study " + stN + " in the study group " + gName + " is unknown")

    
    def get_study_names(self):
        return sorted(self._studies.keys())
    
    def get_study_group_names(self):
        return sorted(self._studyGroups.keys())

    def get_study(self,name):
        def prepare(study):
            if not study._loaded:
                study._load_family_data()
            return study
        if name in self._studies:
            return prepare(self._studies[name])
        if name in self._studyGroups:
            if len(self._studyGroups[name].studyNames)!=1:
                raise Exception('get_study can only use study groups with only one study')
            return prepare(self._studies[self._studyGroups[name].studyNames[0]])
        raise Exception('unknown study ' + name)
        
    def get_studies(self,definition):
        sts = []

        def prepare(study):
            if not study._loaded:
                study._load_family_data()
            sts.append(study)
            
        for name in definition.split(","):
            if name in self._studies:
                prepare(self._studies[name])
            if name in self._studyGroups:
                for sName in self._studyGroups[name].studyNames:
                    prepare(self._studies[sName])
        return sts
                
    def get_study_group(self, gName):
        if gName not in self._studyGroups:
            raise Exception("Unknown study group " + gName)
        return self._studyGroups[gName]
    
    def get_denovo_variants(self, studies, **filters):
        seenVs = set()
        if isinstance(studies,str):
            studies = self.get_studies(studies) 
        for study in studies:
            for v in study.get_denovo_variants(**filters):
                vKey = v.familyId + v.location + v.variant
                if vKey in seenVs:
                    continue
                yield v
                seenVs.add(vKey)
                

    def get_validation_variants(self):
        validationDir = self._config.get('validation', 'dir' )
        studyNames = self._config.get('validation', 'studies' )
        stdies = [self.get_study(x) for x in studyNames.split(',')]

        print >>sys.stderr, "validationDir: |", validationDir, "|"
        print >>sys.stderr, "studyNames: |", studyNames, "|"

        knownFams = {}
        for stdy in stdies:
            for f in stdy.families:
                if f in knownFams:
                    print >> sys.stderr, "Ha, family", f, "is more that one study: ", stdy.name, "and", knownFams[f]
                knownFams[f] = stdy.families[f]

	# print knownFams
        '''
        knownIns = {}
        for v in self.get_denovo_variants(stdies,callSet="dirty"):
            if v.variant.startswith('ins('):
                seq = v.variant[4:-1]
                for ic in reversed(range(len(seq))):
                    if not seq[ic].isdigit():
                        break
                ic+=1
                seq = seq[0:ic]
                iLen = len(seq)
                
                k = "".join((v.familyId,";",v.location,";",str(iLen)))
                if k in knownIns:
                    print >>sys.stderr, 'aaaa: ' + knownIns[k] + " and " + v.variant
                knownIns[k] = v.variant

            
        '''

        nIncompleteIns = 0
        nCompleteIns = 0
        vars = []
        # nvf = open("view-normalized.txt",'w') 
        for fn in glob.glob(validationDir + '/*/reports/report*.txt'):
            print >>sys.stderr, "Working on file:|", fn,"|"
            dt = genfromtxt(fn,delimiter='\t',dtype=None,names=True, case_sensitive=True)
            # if there is only row of data in the file then the genfromtxt function returns a 0d array.
            # this causes an error when trying to iterate over it, so it must be converted to a 1d array
            if dt.ndim==0:
                dt=dt.reshape(1)
                
            batchId = dirname(fn).split("/")[-2]
                        
            for dtR in dt:
                class ValidationVariant:
                    @property
                    def bestSt(self):
                        try:
                            return self._bestSt
                        except AttributeError:
                            self._bestSt = str2Mat(self.bestStS, colSep=" ")
                            return self._bestSt
                    @property
                    def valBestSt(self):
                        try:
                            return self._valBestSt
                        except AttributeError:
                            self._valBestSt = str2Mat(self.valBestStS, colSep=" ")
                            return self._valBestSt
                    @property
                    def valCounts(self):
                        try:
                            return self._valCounts
                        except AttributeError:
                            self._valCounts= str2Mat(self.valCountsS, colSep=" ")
                            return self._valCounts
                    @property
                    def inChS(self):
                        mbrs = self.memberInOrder
                        bs = self.bestSt
                        childStr = ''
                        for c in xrange(2,len(mbrs)):
                            if bs[1][c]:
                                childStr += (mbrs[c].role + mbrs[c].gender)
                        return childStr

                v = ValidationVariant()

                v.batchId = batchId 
                v.atts = { x: dtR[x] for x in dt.dtype.names }

                v.familyId = str(dtR['familyId'])
                v.location = dtR['location']
                v.variant = dtR['variant']
                v.bestStS = dtR['bestState']
                v.resultNote = dtR['valnote']

                try:
                    v.why = dtR['why']
                except:
                    v.why = "???"
            
                try:
                    v.who = dtR['who']
                except:
                    v.who = "???"

                v.valCountsS = dtR['valcounts']
                v.valBestStS = dtR['valbestState']
                v.valStatus = dtR['valstatus']


                v.valParent = ""
                if 'valparent' in dtR:
                    v.valParent = dtR['valparent']

                if v.familyId in knownFams:
                    v.memberInOrder = knownFams[v.familyId].memberInOrder
                else:
                    v.memberInOrder = []
                    print >>sys.stderr, "Breh, the family", v.familyId, "is unknown"


                # nvf.write("\t".join((v.familyId,v.location,v.variant,v.bestStS,v.who,v.why,v.batchId,v.valCountsS,v.valBestStS,v.valStatus,v.resultNote,v.valParent)) + "\n")
                vars.append(v)
        # nvf.close()
        print >>sys.stderr, "nIncompleteIns:", nIncompleteIns
        print >>sys.stderr, "nCompleteIns:", nCompleteIns
        return vars

    def get_denovo_sets(self,dnvStds):
        r = GeneTerms()
        r.geneNS = "sym"

        def getMeasure(mName):
            from DAE import phDB
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

        nvIQ = getMeasure('pcdv.ssc_diagnosis_nonverbal_iq') 

        def addSet(setname, genes,desc=None):
            if desc:
                r.tDesc[setname] = desc
            else:
                r.tDesc[setname] = setname
            for gSym in genes:
                r.t2G[setname][gSym]+=1
                r.g2T[gSym][setname]+=1
        def genes(inChild,effectTypes,inGenesSet=None,minIQ=None,maxIQ=None):
            if inGenesSet:
                vs = self.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild,geneSyms=inGenesSet)
            else:
                vs = self.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild)
            if not (minIQ or maxIQ):
                return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
            if minIQ:
                return {ge['sym'] for v in vs for ge in v.requestedGeneEffects if v.familyId in nvIQ and nvIQ[v.familyId]>=minIQ }
            if maxIQ:
                return {ge['sym'] for v in vs for ge in v.requestedGeneEffects if v.familyId in nvIQ and nvIQ[v.familyId] < maxIQ }

        def set_genes(geneSetDef):
            gtId,tmId = geneSetDef.split(":")
            return set(self._giDB.getGeneTerms(gtId).t2G[tmId].keys())

        def recSingleGenes(inChild,effectTypes):
            vs = self.get_denovo_variants(dnvStds,effectTypes=effectTypes,inChild=inChild)

            gnSorted = sorted([[ge['sym'], v] for v in vs for ge in v.requestedGeneEffects ]) 
            sym2Vars = { sym: [ t[1] for t in tpi] for sym, tpi in groupby(gnSorted, key=lambda x: x[0]) }
            sym2FN = { sym: len(set([v.familyId for v in vs])) for sym, vs in sym2Vars.items() } 
            return {g for g,nf in sym2FN.items() if nf>1 }, {g for g,nf in sym2FN.items() if nf==1 }

        recPrbLGDs, sinPrbLGDs = recSingleGenes('prb' ,'LGDs')
        addSet("recPrbLGDs",     recPrbLGDs)
        addSet("sinPrbLGDs",     sinPrbLGDs) 

        addSet("prbLGDs",           genes('prb' ,'LGDs'))
        addSet("prbMaleLGDs",       genes('prbM','LGDs'))
        addSet("prbFemaleLGDs",     genes('prbF','LGDs'))

        addSet("prbLGDsInFMR1",     genes('prb','LGDs',set_genes("main:FMR1-targets")))
        # addSet("prbLGDsInCHDs",     genes('prb','LGDs',set("CHD1,CHD2,CHD3,CHD4,CHD5,CHD6,CHD7,CHD8,CHD9".split(','))))

        addSet("prbMissense",       genes('prb' ,'missense'))
        addSet("prbMaleMissense",   genes('prbM' ,'missense'))
        addSet("prbFemaleMissense", genes('prbF' ,'missense'))
        addSet("prbSynonymous",     genes('prb' ,'synonymous'))

        addSet("sibLGDs",           genes('sib' ,'LGDs'))
        addSet("sibMissense",       genes('sib' ,'missense'))
        addSet("sibSynonymous",     genes('sib' ,'synonymous'))

        addSet("A",      recPrbLGDs, "recPrbLGDs")
        addSet("B",      genes('prbF','LGDs'), "prbF")
        addSet("C",      genes('prb','LGDs',set_genes("main:FMR1-targets")), "prbFMRP")
        addSet("D",      genes('prb','LGDs',maxIQ=90),"prbML")
        addSet("E",      genes('prb','LGDs',minIQ=90),"prbMH")

        addSet("AB",     set(r.t2G['A']) | set(r.t2G['B'])) 
        addSet("ABC",    set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C'])) 
        addSet("ABCD",   set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C'])  | set(r.t2G['D']) )
        addSet("ABCDE",   set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C'])  | set(r.t2G['D']) | set(r.t2G['E']) )
        return r
   

    ### THE ONES BELOW SHOULD BE MOVED 
    # return a list of valid variant types, add None to this list for the UI

    def effectTypesSet(self,effectTypesS):
        return get_effect_types_set(effectTypesS)
        '''
        if effectTypesS == "CNVs":
            return { "CNV+", "CNV-" }
        if effectTypesS == "LGDs":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop" }    
        if effectTypesS == "nonsynonymous":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop",
                    "missense", "no-frame-shift" }
        return set(effectTypesS.split(","))
        '''
                          
            
def str2Mat(matS, colSep=-1, rowSep="/", str2NumF=int):
    # print matS, colSep, rowSep, str2NumF 
    if colSep == -1:
        return np.array([ [ str2NumF(c) for c in r ] for r in matS.split(rowSep) ])
    return np.array([ [ str2NumF(v) for v in r.split(colSep) ] for r in matS.split(rowSep) ])

def mat2Str(mat, colSep=" ", rowSep="/"):
    return rowSep.join([ colSep.join([str(n) for n in mat[i,:]]) for i in xrange(mat.shape[0])  ])

# added sep param in order to produce CSV outout for Web Site
def _safeVs(tf,vs,atts=[],sep="\t"):
    def ge2Str(gs):
        return "|".join( x['sym'] + ":" + x['eff'] for x in gs)

    mainAtts = "familyId studyName location variant bestSt fromParentS inChS counts geneEffect requestedGeneEffects popType".split()
    specialStrF = {"bestSt":mat2Str, "counts":mat2Str, "geneEffect":ge2Str, "requestedGeneEffects":ge2Str}

    tf.write(sep.join(mainAtts+atts)+"\n") 
    for v in vs:
        mavs = []
        for att in mainAtts:
            try:
                if att in specialStrF:
                    mavs.append(specialStrF[att](getattr(v,att)))
                else:
                    mavs.append(str(getattr(v,att)))
            except:
                mavs.append("")
                 
        tmp = sep.join(mavs + [str(v.atts[a]).replace(sep, ';') if a in v.atts else "" for a in atts])   
        tf.write(tmp +"\n")

def viewVs(vs,atts=[]):
    tf = tempfile.NamedTemporaryFile("w", delete=False)
    print >>sys.stderr, "temp file name: " + tf.name
    _safeVs(tf,vs,atts)
    tf.close()
    os.system("oocalc " + tf.name)
    os.remove(tf.name)

def safeVs(vs,fn,atts=[]):
    if fn=="-":
        f = sys.stdout
    else:
        f = open(fn,"w")
    _safeVs(f,vs,atts)
    if fn!="-":
        f.close()

def normalRefCopyNumber(location,gender):
    clnInd = location.find(":")
    chr = location[0:clnInd]

    if chr in ['chrX', 'X', '23', 'chr23']:
        if '-' in location:
            dshInd = location.find('-')
            pos = int(location[clnInd+1:dshInd])
        else:
            pos = int(location[clnInd+1:])

        # hg19 pseudo autosomes region: chrX:60001-2699520 and chrX:154931044-155260560 
        if pos < 60001 or (pos>2699520 and pos < 154931044) or pos > 155260560:
            if gender=='M':
                return 1
            elif gender!='F':
                raise Exception('weird gender ' + gender)
    elif chr in ['chrY', 'Y', '24', 'chr24']:
        if gender=='M':
            return 1
        elif gender=='F':
            return 0
        else:
            raise Exception('gender needed')
    return 2

def isVariant(bs,c,location=None,gender=None):
    normalRefCN=2

    if location:
        normalRefCN = normalRefCopyNumber(location,gender)

    if bs[0,c] != normalRefCN or any([bs[o,c]!=0 for o in xrange(1,bs.shape[0])]): 
        return True
    return False
        

def parseGeneEffect(effStr):
    geneEffect = []
    if effStr == "intergenic":
        return geneEffect 

    # HACK!!! To rethink
    if effStr in ["CNV+", "CNV-"]:
        geneEffect.append({'sym':"", 'eff':effStr})
        return geneEffect
      
    for ge in effStr.split("|"):
        cs = ge.split(":");
        if len(cs) != 2:
            raise Exception(ge + " doesn't agree with the <sym>:<effect> format");
        sym,eff = cs
        geneEffect.append({'sym':sym, 'eff':eff})
    return geneEffect

def filter_gene_effect(geneEffects, effectTypes, geneSyms):
    if not effectTypes:
        return [x for x in geneEffects if x['sym'] in geneSyms]
    if not geneSyms:
        return [x for x in geneEffects if x['eff'] in effectTypes]
    return [x for x in geneEffects if x['eff'] in effectTypes and  x['sym'] in geneSyms]

if __name__ == "__main__":
    wd = os.environ['DAE_DB_DIR']
    print "wd:", wd
    from Sfari import SfariCollection

    sfariDB = SfariCollection(os.environ['PHENO_DB_DIR'])
    vDB = VariantsDB(wd,sfariDB=sfariDB)

    for v in vDB.get_validation_variants():
        # pass
	print v.familyId,v.location,v.variant,v.valStatus


    '''
    st = vDB.get_study('wig683')

    v = st.get_transmitted_variants().next()

    # st = vDB.get_study('LevyCNV2011')
    for v in st.get_denovo_variants():
        if v.inChS != v.atts['inChild']:
            print v.familyId, "".join([str(v.get_normal_refCN(c)) for c in xrange(v.bestSt.shape[1])]), "\t", mat2Str(v.bestSt), "    \t", v.inChS, v.atts['inChild'], v.location, v.variant, "   \t", [(p.role, p.gender) for p in v.study.families[v.familyId].memberInOrder]
    '''
    '''
    st = vDB.get_study('wig683')

    for v in st.get_transmitted_summary_variants(minParentsCalled=0,maxAltFreqPrcnt=-1, regionS="10:90000-94000"):
        print "SUMMARY:", v.location, v.variant

    for v in st.get_transmitted_variants(minParentsCalled=0,maxAltFreqPrcnt=-1, regionS="10:92990-92990"):
        print "FAMILY :", v.location, v.variant, v.familyId

    '''
    # rs = vDB.get_study('wigRNASeq')
    # viewVs(vDB.get_study('wig683').get_denovo_variants(effectTypes="LGDs"))

    # print "OOOOOOOOO", len(list(vDB.get_denovo_variants([vDB.get_study("DalyWE2012"), vDB.get_study("EichlerWE2012"), vDB.get_study("wig683")], effectTypes="LGDs", inChild="prb")))
    # sd = vDB.get_study("DalyWE2012")
    # sd = vDB.get_study("EichlerWE2012")
    # sd = vDB.get_study("StateWE2012")
    # sd = vDB.get_study("LevyCNV2011")
    # sd = vDB.get_study("wig683")

    # for tt in [(x.familyId, x.location, x.bestSt,x.atts['inChild']) for x in sd.get_denovo_variants(inChild="sib")]:
    #    print tt


'''
    fo = open("CHD5-nv.txt","w")
    fo.write("\t".join("mikesEncoding familyId location variant bestSt counts familyGenderType " 
                     "fromParent inChildren popType altFreqPrcnt effectType effectGene effectDetails".split()) + "\n")

    for v in sd.get_transmitted_variants(maxAltFreqPrcnt=1.0,geneSyms={"CHD5"}):
        bs = v.bestSt
        mbrs = sd.families[v.familyId].memberInOrder

        parentStr = ''
        childStr = ''
        if bs[1][0]:
            parentStr += "mom"
        if bs[1][1]:
            parentStr += "dad"
        for c in xrange(2,len(mbrs)):
            if bs[1][c]:
                childStr += (mbrs[c].role + mbrs[2].gender)

        mikesEncoding = "[M%d F%d A%s%d S%s%d]" % (bs[1,0], bs[1,1], mbrs[2].gender, bs[1,2], mbrs[3].gender, bs[1,3])

        fo.write("\t".join((mikesEncoding, v.familyId, v.location, v.variant, v.bestStStr, v.countsStr, 
            sd.families[v.familyId].memberInOrder[2].gender+sd.families[v.familyId].memberInOrder[3].gender, 
            parentStr, childStr,
            v.popType, str(v.altFreqPrcnt), v.atts['effectType'], v.atts['effectGene'], v.atts['effectDetails'])) + "\n")
    fo.close()
'''         
    
    # vDB.getDenovoVariants('wigler582')
    # vDB.getDenovoVariants('3papers')
    # 
    # res = vDB.getDenovoVariantsGeneSyms('wig582-3pap',inChildRole='prb', effectTypes="LGDs")
    # right = set()
    # for l in open(wd + '/rightPrbLGDs.txt'):
    #     right.add(l.strip())

    # print len(res), len(right)
    # print 'res but not right:', " ".join([g for g in res if not g in right])
    # print 'right but not res:', " ".join([g for g in right if not g in res])

    # print "\n".join(["\t".join((v.center, v.geneEffect[0]['sym'], v.majorEffect)) 
    #                 for v in vDB.getDenovoVariants('wig582-3pap',effectTypes="LGDs")
    #                 ])
