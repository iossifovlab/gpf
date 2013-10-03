
from DAE import *

import ConfigParser

from GenomeAccess import openRef
from GeneModelFiles import load_gene_models

'''
GA = genomesDB.get_GA()
GA = genomesDB.getGA("hg19")
?? GA = genomesDB.getGA("/data/unsafe/autism/genomes/hg19/chrAll.fa") ??
GA = GA("/data/unsafe/autism/genomes/hg19/chrAll.fa")

GA.get_seq("1",151235,1414)


gmDB = genomesDB.get_gene_models_db() # default genome default geneModels
gmDB = genomesDB.get_gene_models_db("CCDS") # default genome given geneModels

gmDB = genomesDB.get_gene_models_db(genome='hg19') # given genome default models
gmDB = genomesDB.get_gene_models_db("CCDS", genome='hg19') # given genome default models

gmDB = GeneModels("/home/ivan/ccdsGene.txt.gz",geneMappingFile="")
gmDB.....
'''

class GenomesDB:
    def __init__(self, daeDir, confFile=None):
        
        self.daeDir = daeDir
        if not confFile:
            confFile = daeDir + "/genomesDB.conf"

        self.config = ConfigParser.SafeConfigParser({'wd':daeDir})
        self.config.optionxform = lambda x: x
        self.config.read(confFile)

        self.defaultGenome = self.config.get('genomes', 'defaultGenome')
        self._geneModels = {}

    def get_genome(self, genomeId=None):
        if not genomeId:
            genomeId = self.defaultGenome
        genomeFile = self.config.get('genome.' + genomeId, 'chrAllFile')
        # print "AAAAAAAAAAAAAA: genomeId:", genomeId, "genomeFile:", genomeFile
        return openRef(genomeFile)

    def get_gene_models(self, geneModelId=None, genomeId=None):
        if not genomeId:
            genomeId = self.defaultGenome
        if not geneModelId:
            geneModelId = self.config.get('genome.' + genomeId, 'defaultGeneModel')
        key = genomeId + geneModelId
        if key not in self._geneModels:
            geneModelFile = self.config.get('genome.' + genomeId, 'geneModel.' + geneModelId + '.file')
            gmDb = load_gene_models(geneModelFile)
            self._geneModels[key] = gmDb
        return self._geneModels[key]
    
# GA = genomesDB.get_GA()
# GA = genomesDB.getGA("hg19")

        
