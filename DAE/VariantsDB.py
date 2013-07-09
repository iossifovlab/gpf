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

class Study:
    def __init__(self, vdb, name, load=True):
        self.vdb = vdb
        self.name = name
        self.configSection = 'study.' + name
        self.dnvData = {}
                
        if self.vdb.config.has_option(self.configSection,'denovoCalls.files'):
            self._has_denovo = True
        else:                     
            self._has_denovo = False

        if self.vdb.config.has_option(self.configSection,'transmittedVariants.indexFile'):
            self._has_transmitted = True
        else:                     
            self._has_transmitted = False
        
        self._description = ""

        if load:
            self._loaded = True
            self._load_family_data()            
        else: 
            self._loaded = False
            
    @property
    def loaded(self):
        return self._loaded
                
    @property
    def has_denovo(self):
        return self._has_denovo
         
    @property
    def has_transmitted(self):
        return self._has_transmitted

    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, value):
        self._description = value
    
    def get_transmitted_summary_variants(self,minParentsCalled=600,maxAltFreqPrcnt=5.0,minAltFreqPrcnt=-1,variantTypes=None, effectTypes=None,ultraRareOnly=False, geneSyms=None, regionS=None):
        
        if self.loaded==False:
            self._load_family_data()
                    
        transmittedVariantsFile = self.vdb.config.get(self.configSection, 'transmittedVariants.indexFile' ) + ".txt.bgz"
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
        
        if self.loaded==False:
            self._load_family_data()
                    
        transmittedVariantsTOOMANYFile = self.vdb.config.get(self.configSection, 'transmittedVariants.indexFile' ) + "-TOOMANY.txt.bgz"

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

        if self.loaded==False:
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
        
        if callSet in self.dnvData:
            return self.dnvData[callSet]
 
        flsS = self.vdb.config.get(self.configSection, propName)
        varList = []
        for fl in flsS.split('\n'):
            print >> sys.stderr, "Loading file", fl, "for collection ", self.name 
            dt = genfromtxt(fl,delimiter='\t',dtype=None,names=True,
                            case_sensitive=True)

            hasCenter = 'center' in dt.dtype.names;
            for vr in dt:
                atts = { x: vr[x] for x in dt.dtype.names }
                if not hasCenter:
                    atts['center'] = "CSHL"

                v = Variant(atts,bestStColSep=" ")
                v.popType = "denovo"
                v.study = self
                varList.append(v)

        self.dnvData[callSet] = varList
        return varList


    def _load_family_data(self):
        fdFile = self.vdb.config.get(self.configSection, "familyInfo.file" )
        fdFormat = self.vdb.config.get(self.configSection, "familyInfo.fileFormat" )
   
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
        self.loaded=True
        
    def _load_family_data_SSCFams(self, reportF):
        rf = open(reportF)
        families = {l.strip():Family() for l in rf}
        for f in families.values():    
            f.memberInOrder = []

        rlsMp = { "mother":"mom", "father":"dad", "proband":"prb", "designated-sibling":"sib", "other-sibling":"sib" }
        genderMap = {"female":"F", "male":"M"}

        for indS in self.vdb.sfariDB.individual.values():
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
        for indId,indS in self.vdb.sfariDB.individual.items():
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
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments=None)
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

        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments=None)

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
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True,comments=None)

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
        dt = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True, comments=None)

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
        families = {}
        badFamilies = {}
        qrp = genfromtxt(reportF,delimiter='\t',dtype=None,names=True, case_sensitive=True)
        for qrpR in qrp:
            f = Family()
            f.familyId = qrpR['quadquad_id'][5:10]
            f.atts = { x:qrpR[x] for x in qrp.dtype.names }

            def piF(pi):
                sfariDB = self.vdb.sfariDB
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

# This class is used to read the variantDB.conf without actually loading 
# any of the studies.
class VariantsConfig:
    def __init__(self, vdb, wd, confFile):
                    
        self.vdb = vdb
        
        self._config = ConfigParser.SafeConfigParser({'wd':wd})            
        self._config.optionxform = lambda x: x
        
        if not confFile:
            confFile = wd + "/variantDB.conf"
            
        self._config.read(confFile)
        
        self._studies = {}
        self._study_groups = {}
        
        
    @property
    def studies(self):
        return self._studies

    @property
    def study_groups(self):
        return self._study_groups
    
    @property
    def config(self):
        return self._config
            
    # this method loads Study Groups into a dictionary
    # and load the meta data about each study, but does
    # not load the actual study data.
    def processConfig(self):        
        self.processStudies()
        self.processStudyGroups()
        
    # this function loads the study group names into a dictionary
    # of lists of study names
    def processStudyGroups(self):
        self._study_groups = {}
        
        groupNames = self._config.options('studyGroups')
        
        for name in groupNames:
            if name == 'wd':
                continue
            studies = self._config.get('studyGroups', name)             
            studyList = [s for s in studies.split(",")]
            self._study_groups[name] = studyList
        
    # this function creates and entry for each study
    # but does not load the actual data.                    
    def processStudies(self):
        self._studies={}
        
        for sn in self.config.sections():
            if sn.startswith('study.'):                
                name = sn[6:]
                self._studies[name] = Study(self.vdb,name,load=False)
                
                notes = []

                m = re.search('WE', name)                
                if m:
                    notes.append('Whome Exome')

                m = re.search('TG', name)
                if m:
                    notes.append('Targeted Sequencing')

                m = re.search('Eichler', name)
                if m:
                    notes.append('Eichler Lab')

                m = re.search('Daly', name)
                if m:
                    notes.append('Daly Lab')

                m = re.search('State', name)
                if m:
                    notes.append('State Lab')

                m = re.search('Iossifov', name)
                if m:
                    notes.append('Wigler Lab')

                m = re.search('Levy', name)
                if m:
                    notes.append('Wigler Lab')

                m = re.search('^wig', name)                
                if m:
                    notes.append('data was re-processed using CSHL pipeline')
                
                    
                'Send','Data which can be sent to a collaborator'
                'Published','Data was published'
                
                self._studies[name].description = ', '.join(notes)


class VariantsDB:
    def __init__(self, daeDir, confFile=None, sfariDB=None, giDB=None):
        
        self.daeDir = daeDir
        self.variantDir = os.path.join(daeDir, "variantdb")
        self.giDir = os.path.join(daeDir, "geneinfodb")
        self.phenoDir = os.path.join(daeDir, "phenodb")
        
        self._VariantsConfig = VariantsConfig(self, daeDir, confFile)
        self.config = self._VariantsConfig.config
        
        self.dnvCols = {}
        self.pardata = []
        #self._studies = {}
        self.sfariDB = sfariDB
        self.giDB = giDB
        
        # vdb (self) is used all over the place, so the call to 
        # process the config needs to go last to make sure all
        # the required variables are initialized 
        self._VariantsConfig.processConfig()


    @property
    def studies(self):
        return self._VariantsConfig.studies

    @property
    def study_groups(self):
        return self._VariantsConfig.study_groups
    
    
    # return a list of valid variant types, add None to this list for the UI
    def get_variant_types(self):
        types = ['All', 'CNV+', 'CNV-', 'snv', 'ins', 'del']
        return types


    # return a list of valid effect types, add None to this list for the UI
    def get_effect_types(self):
        types = ['All', 
                 'LGDs', 
                 'CNVs', 
                 'nonsynonymous',
                 'CNV-',
                 'CNV+',
                 'frame-shift',
                 'intron',
                 'no-frame-shift-new-stop',
                 'synonymous',
                 'nonsense',
                 'no-frame-shift',
                 'missense',
                 "3'UTR",
                 "5'UTR",
                 'splice-site']
        return types
                          
    def get_child_types(self):
        types = ['prb',
                 'sib',
                 'prbM', 
                 'sibF', 
                 'sibM', 
                 'prbF',
                 #'prbMsibM',
                 #'prbMsibF'
                 ]
        return types
                                
    def get_study_names(self):
        return [sn[6:] for sn in self.config.sections() if sn.startswith('study.')]    
    
    def getDenovoStudies(self):
        names=[]

        for studyKey,study in self.studies.items():
            if study.has_denovo:
                names.append(studyKey)

        names = sorted(names)
                
        return names
    
    
    def getStudyGroups(self):
        names=[]

        for studyKey,study in self.study_groups.items():
            if studyKey != 'wd':
                names.append(studyKey)

        names = sorted(names)
                
        return names    
    
        
    # returns a sorted list of study names, that have the transmittedVariants.indexFile option
    # in their section
    # does not return the group names yet
    # I'd need tp parse the list and make sure all the studies are just Transmitted and contain no denovo
    
    def getTransmittedStudies(self):
        studies=[]

        for sn in self.config.sections():
            if sn.startswith('study.'):
                if self.config.has_option(sn,'transmittedVariants.indexFile'):
                    studies.append(sn[6:])

        studies = sorted(studies)
            
        return studies
        
    def get_study(self,name):
        
        if name in self._VariantsConfig.studies:
            study = self._VariantsConfig.studies[name]
            if study.loaded == False:
                study._load_family_data()
            return study
        else:
            return None
            
        #if name not in self._studies:
        #    self._studies[name] = Study(self, name)
        #return self._studies[name]
        
        
    def get_studies(self,definition):
        try:
            studiesS = self.config.get('studyGroups', definition)
        except:
            studiesS = definition 
        return [self.get_study(s) for s in studiesS.split(",")]
    
    def effectTypesSet(self,effectTypesS):
        if effectTypesS == "CNVs":
            return { "CNV+", "CNV-" }
        if effectTypesS == "LGDs":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop" }    
        if effectTypesS == "nonsynonymous":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop",
                    "missense", "no-frame-shift" }
        return set(effectTypesS.split(","))

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
        validationDir = self.config.get('validation', 'dir' )
        studyNames = self.config.get('validation', 'studies' )
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
                v.why = dtR['why']
                v.who = dtR['who']
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
                    print "Breh, the family", v.familyId, "is unknown"


                # nvf.write("\t".join((v.familyId,v.location,v.variant,v.bestStS,v.who,v.why,v.batchId,v.valCountsS,v.valBestStS,v.valStatus,v.resultNote,v.valParent)) + "\n")
                vars.append(v)
        # nvf.close()
        print >>sys.stderr, "nIncompleteIns:", nIncompleteIns
        print >>sys.stderr, "nCompleteIns:", nCompleteIns
        return vars


    def getDenovoVariantsGeneSyms(self,collection, nChildren=None, inChildRole=None, inChildSex=None, effectTypes=None):
        if isinstance(effectTypes,str):
            effectTypes = self.effectTypesSet(effectTypes)
        r = set()
        for v in self.getDenovoVariants(collection, nChildren,inChildRole,inChildSex, effectTypes):
            for ge in v.geneEffect:
                if effectTypes==None or ge['eff'] in effectTypes:
                    r.add(ge['sym'])

        return r

    def getDenovoVariantsWithGeneSyms(self,collection, nChildren=None, inChildRole=None, inChildSex=None, effectTypes=None):
        if isinstance(effectTypes,str):
            effectTypes = self.effectTypesSet(effectTypes)
        r = []
        for v in self.getDenovoVariants(collection, nChildren,inChildRole,inChildSex, effectTypes):
            geneSyms = set()
            for ge in v.geneEffect:
                if effectTypes==None or ge['eff'] in effectTypes:
                    geneSyms.add(ge['sym'])
            r.append({'var':v,'geneSyms':geneSyms})

        return r

    def getDenovoVariants(self,collection, nChildren=None, inChildRole=None, inChildSex=None, effectTypes=None):
        if not collection in self.dnvCols:
            self.loadDnvCollection(collection)
        if nChildren==None and inChildRole==None and inChildSex==None and effectTypes==None:
            return self.dnvCols[collection]
        r = []
        if isinstance(effectTypes,str):
            effectTypes = self.effectTypesSet(effectTypes)
        for v in self.dnvCols[collection]:
            if nChildren != None and nChildren != len(v.children): 
                continue
            if inChildRole != None and inChildSex == None:
                if not inChildRole in { x['role'] for x in v.children }:
                    continue;
            if inChildSex != None and inChildRole == None:
                if not inChildSex in { x['sex'] for x in v.children }:
                    continue;
            if inChildRole != None and inChildSex != None:
                ok = 0
                for ch in v.children:
                    if ch['role'] == inChildRole and ch['sex'] == inChildSex:
                        ok = 1
                        break
                if ok == 0:
                    continue
            if effectTypes != None:
                ok = 0
                for ge in v.geneEffect:
                    if ge['eff'] in effectTypes:
                        ok = 1
                        break;
                if ok == 0:
                    continue
            r.append(v)
        return r
                

    def loadDnvCollection(self,collection):
        flsS = self.config.get('denovoVariants', 'col.' + collection )
        varList = []
        for fl in flsS.split('\n'):
            print >> sys.stderr, "Loading file", fl, "for collection ", collection    
            dt = genfromtxt(fl,delimiter='\t',dtype=None,names=True,
                            case_sensitive=True)

            hasCenter = 'center' in dt.dtype.names;
            for vr in dt:
                v = DnvVariant()
                if hasCenter:
                    v.center = vr['center'];
                else:
                    v.center = "CSHL"
                v.familyId = vr['familyId']    
                v.location = vr['location']    
                v.majorEffect = vr['effectType']    
                v.inChS = vr['inChild']
                # parsing inChild
                inChS = vr['inChild']
                if len(inChS) == 0 or len(inChS) % 4 != 0: 
                    raise Exception("Unparsable inChild value " + inChS);
                v.children = []
                for i in xrange(0,len(inChS), 4):
                    v.children.append({'role':inChS[i:i+3], 'sex':inChS[i+3]})
                for ch in v.children:
                    if ch['role'] not in {"prb", "sib"}:
                        raise Exception("unrecognized child role: " + ch['role']);
                    if ch['sex'] not in {"M", "F", "?"}:
                        raise Exception("unrecognized child sex: " + ch['sex']);
                # parsing effectGene 
                v.geneEffect = []
                if v.majorEffect != "intergenic":
                    for ge in vr['effectGene'].split("|"):
                        cs = ge.split(":");
                        if len(cs) != 2:
                            raise Exception(ge + " doesn't agree with the <sym>:<effect> format");
                        sym,eff = cs
                        v.geneEffect.append({'sym':sym, 'eff':eff})
        
                varList.append(v)

        self.dnvCols[collection] = varList


    def loadParentData(self):
        if len(self.pardata)>0:
            return;
        parentDataFile = self.config.get('parentVariants', 'summaryFile' )
        print >> sys.stderr, "Loading the parents variants summary from ", parentDataFile 
        self.pardata = genfromtxt(parentDataFile,delimiter='\t',dtype=None,names=True,case_sensitive=True)



    def getUltraRareLGDsInParents(self):
        self.loadParentData()
        effectTypes = set(['splice_site', 'nonsense'])
        r = []

        for vr in self.pardata:
            if vr['altCnt'] != 1 or vr['parentsCalledCnt'] < 300 or not vr['EffectType'] in effectTypes:
                continue
            v = ParentVariant()
            v.location = str(vr['chr'])+":"+str(vr['pos'])
            v.effectType = vr['EffectType']
            v.geneEffect = []
            geneSyms = set()
            for ge in vr['EffectGenes'].split("|"):
                cs = ge.split(":");
                if len(cs) != 2:
                        raise Exception(ge + " doesn't agree with the <sym>:<effect> format");
                sym,eff = cs
                v.geneEffect.append({'sym':sym, 'eff':eff})
                if eff in effectTypes:
                    geneSyms.add(sym)

            r.append({'var':v,'geneSyms':geneSyms})
        return r
                

    
    def getUltraRareSynoymousInParents(self):
        self.loadParentData()
        r = []
        for vr in self.pardata:
            if vr['altCnt'] != 1 or vr['parentsCalledCnt'] < 300 or vr['EffectType'] != "synonymous":
                continue
            v = ParentVariant()
            v.location = str(vr['chr'])+":"+str(vr['pos'])
            v.geneEffect = []
            geneSyms = set()
            for ge in vr['EffectGenes'].split("|"):
                cs = ge.split(":");
                if len(cs) != 2:
                        raise Exception(ge + " doesn't agree with the <sym>:<effect> format");
                sym,eff = cs
                v.geneEffect.append({'sym':sym, 'eff':eff})
                if eff == "synonymous":
                    geneSyms.add(sym)

            r.append({'var':v,'geneSyms':geneSyms})
        return r

    
            
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
