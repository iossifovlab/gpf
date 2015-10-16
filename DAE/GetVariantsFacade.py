import itertools
import sys

from DAE import *


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

def mapToFacade(facadeMap, args):
    mappedArgs = {}
       
    for tuple in facadeMap:
        if tuple[1] in args:
            mappedArgs[tuple[0]] = args[tuple[1]]
        
    return mappedArgs

class GetVariantsFacade:

    def __init__(self, args=None):

        if "denovoStudies" in args:
            self.setDenovoStudies(args["denovoStudies"])        
        else: 
            self.denovoStudies = None

        if "inChild" in args:
            self.setInChild(args["inChild"])        
        else: 
            self.inChild = None

        if "variantTypes" in args:
            self.setVariantTypes(args["variantTypes"])        
        else: 
            self.variantTypes = None
            
        if "effectTypes" in args:
            self.setEffectTypes(args["effectTypes"])        
        else: 
            self.effectTypes = None
        
        if "families" in args:
            self.setFamiliesList(args["families"])        
        else: 
            self.families = None

        if "geneSym" in args:
            self.setGeneSym(args["geneSym"])        
        else: 
            self.geneSyms = None            
                            
        self.regionS = None
        
        if "transmittedStudy" in args:
            self.setTransmittedStudies(args["transmittedStudy"])        
        else: 
            self.transmittedStudies = None
                        

        if "transmittedType" not in args:
            args['transmittedType'] = None

        if "maxAlleleFreqRare" not in args:
            args['maxAlleleFreqRare'] = 1.0            

        if "minAlleleFreqInterval" not in args:
            args['minAlleleFreqInterval'] = 1.0            

        if "maxAlleleFreqInterval" not in args:
            args['maxAlleleFreqInterval'] = 2.0            


        self.popFrequencyMin = None
        self.popFrequencyMax = None
        self.popMinParentsCalled = 0
        self.ultraRare = False

        self.setTransmittedParams(args["transmittedType"],
                                  args["maxAlleleFreqRare"],
                                  args["minAlleleFreqInterval"],
                                  args["maxAlleleFreqInterval"])            

        

            
    def setFamiliesFile(self, familiesFile):
        if familiesFile:
            self.families = loadTextColumn(familiesFile)
        else:
            self.families = None

    def setFamiliesList(self, familiesList):
        if familiesList:
            self.families = familiesList.split(",")
        else: 
            self.families = None
            
    def setGeneSym(self, geneSym):
        if geneSym:
            self.geneSyms = set(geneSym.split(","))
        else: 
            self.geneSyms = None

    def setGeneSymFile(self, geneSymFile):
        if geneSymFile:
            self.geneSyms = set(loadTextColumn(geneSymFile))
        else: 
            self.geneSyms = None


    def setGeneId(self, geneId):
        if geneId:
            self.geneIds = set(geneId.split(","))

            if self.geneIds:
                self.geneSyms = { giDB.genes[x].sym for x in self.geneIds if x in giDB.genes }


    def setGeneIdFile(self, geneIdFile):
        if geneIdFile:
            self.geneIds = set(loadTextColumn(geneIdFile))

            if self.geneIds:
                self.geneSyms = { giDB.genes[x].sym for x in self.geneIds if x in giDB.genes }


    def setGeneSet(self, geneSet):

        if geneSet:
            parts = geneSet.split(":")
            if ":" in geneSet:
                ci = geneSet.index(":")
                collection = geneSet[0:ci]
                setId = geneSet[ci+1:] 
            else:
                collection = "main"
                setId = geneSet 

            gts = giDB.getGeneTerms(collection)
            geneSyms = set(gts.t2G[setId].keys())

    def setEffectTypes(self, effectTypes):

        if effectTypes != "none" and effectTypes != "All":
            self.effectTypes = effectTypes
        else:
            self.variantTypes = None

    def setVariantTypes(self, variantTypes):

        if variantTypes != "none" and variantTypes != "All":
            self.variantTypes = variantTypes
        else:
            self.variantTypes = None
            


    def setDenovoStudies(self, denovoStudies):

        if denovoStudies!=None and denovoStudies!= "None" and denovoStudies!= "none" and denovoStudies!= "":
            self.denovoStudies = denovoStudies
        else:
            self.denovoStudies = None


    def setTransmittedStudies(self, transmittedStudies):

        if transmittedStudies!= "None" and transmittedStudies!= "none" and transmittedStudies!= "":
            self.transmittedStudies = transmittedStudies
        else:
            self.transmittedStudies = None

    def setInChild(self, inChild):
        if inChild != "none":
            self.inChild = inChild
        else:
            self.inChild = None
            
    def setPopFrequencyMin(self, popFrequencyMin):
        self.popFrequencyMin = popFrequencyMin

    def setPopFrequencyMax(self, popFrequencyMax):
        self.popFrequencyMax = popFrequencyMax

    def setPopMinParentsCalled(self, popMinParentsCalled):
        self.popMinParentsCalled = popMinParentsCalled

    def setTransmittedParams(self, transmittedType, maxAlleleFreqRare, minAlleleFreqInterval, maxAlleleFreqInterval):
        
        if transmittedType=="all":
            self.popFrequencyMin = -1
            self.popFrequencyMax = -1
            self.ultraRare = False
                        
        elif transmittedType=="ultrarare":
            self.popFrequencyMin = -1
            self.popFrequencyMax = "ultraRare"
            self.ultraRare = True
        
        elif transmittedType=="rare":
            self.popFrequencyMin = -1
            
            try:                
                self.popFrequencyMax = float(maxAlleleFreqRare)
            except: 
                self.popFrequencyMax = 1.0
                
            self.ultraRare = False
        
        elif transmittedType=="interval":
            try:                
                self.popFrequencyMin = float(minAlleleFreqInterval)
            except: 
                self.popFrequencyMin = 0.0

            try:                
                self.popFrequencyMax = float(maxAlleleFreqInterval)
            except: 
                self.popFrequencyMax = 1.0

            self.ultraRare = False
        
        #print 'popFrequencyMin ', self.popFrequencyMin
        #print 'popFrequencyMax ', self.popFrequencyMax
        #print 'ultraRare ', self.ultraRare
                 
    def getVariants(self, output=None):
        
        self.dvs = []
        if self.denovoStudies != None:
            try:
                self.dst = vDB.get_studies(self.denovoStudies)
            except:
                raise Exception("The de novo study: " + self.denovoStudies + " DOES NOT EXIST! ...exiting!")
            
            self.dvs = vDB.get_denovo_variants(self.dst,
                                      inChild=self.inChild,
                                      variantTypes=self.variantTypes,
                                      effectTypes=self.effectTypes,
                                      familyIds=self.families,
                                      geneSyms=self.geneSyms,
                                      regionS=self.regionS)

    

        self.ivs = []
        if self.transmittedStudies != None:
            
#            popFreqMax = -1
#            ultraRare = False 
#            
#            if self.popFrequencyMin==None:
#                self.popFrequencyMin=0
#                
#            if self.popFrequencyMax==None:
#                self.popFrequencyMax=-1
#                                
#            if self.popFrequencyMax=="ultraRare":
#                self.ultraRare = True
#            else:
#                self.ultraRare = False
#                self.popFrequencyMax = float(self.popFrequencyMax)
#
#            if self.popMinParentsCalled==None:
#                self.popMinParentsCalled=0
                
            try:
                self.ist = vDB.get_study(self.transmittedStudies)
            except:
                raise Exception("The transmitted study: " + self.transmittedStudies + " DOES NOT EXIST! ...exiting!")

            self.ivs = self.ist.get_transmitted_variants(variantTypes=self.variantTypes,
                                                    effectTypes=self.effectTypes,
                                                    inChild=self.inChild,
                                                    minParentsCalled=float(self.popMinParentsCalled),
                                                    minAltFreqPrcnt=self.popFrequencyMin,
                                                    maxAltFreqPrcnt=self.popFrequencyMax,
                                                    ultraRareOnly=self.ultraRare,
                                                    familyIds=self.families,
                                                    geneSyms=self.geneSyms,
                                                    regionS=self.regionS)


        if output==None:
            safeVs(itertools.imap(augmentAVar,itertools.chain(self.dvs, self.ivs)),'-',
                   ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'])
        else:
            
            #safeVs2(output,itertools.imap(augmentAVar, self.dvs),
            #        ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'],sep=",")

            safeVs2(output,itertools.imap(augmentAVar,itertools.chain(self.dvs, self.ivs)),
                    ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'],sep=",")
