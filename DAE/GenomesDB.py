from __future__ import unicode_literals

from builtins import object
from builtins import open

# from DAE import *

from configparser import ConfigParser

from GenomeAccess import openRef
from GeneModelFiles import load_gene_models
from RegionOperations import Region

'''
GA = genomesDB.get_GA()
GA = genomesDB.getGA("hg19")
?? GA = genomesDB.getGA("/data/unsafe/autism/genomes/hg19/chrAll.fa") ??
GA = GA("/data/unsafe/autism/genomes/hg19/chrAll.fa")

GA.get_seq("1",151235,1414)


gmDB = genomesDB.get_gene_models_db() # default genome default geneModels
gmDB = genomesDB.get_gene_models_db("CCDS") # default genome given geneModels

gmDB = genomesDB.get_gene_models_db(
    genome='hg19') # given genome default models
gmDB = genomesDB.get_gene_models_db(
    "CCDS", genome='hg19') # given genome default models

gmDB = GeneModels("/home/ivan/ccdsGene.txt.gz",geneMappingFile="")
gmDB.....
'''


class GenomesDB(object):
    def __init__(self, daeDir, confFile=None,):

        self.daeDir = daeDir
        if not confFile:
            confFile = daeDir + "/genomesDB.conf"

        self.config = ConfigParser({
            'wd': daeDir,
        })
        self.config.optionxform = lambda x: x
        with open(confFile, 'r', encoding="utf-8") as infile:
            self.config.read_file(infile)

        self.defaultGenome = self.config.get('genomes', 'defaultGenome')
        self._geneModels = {}
        self._mitoGeneModels = {}

    def get_genome_file(self, genomeId=None):
        if not genomeId:
            genomeId = self.defaultGenome
        genomeFile = self.config.get('genome.' + genomeId, 'chrAllFile')
        return genomeFile

    def get_genome(self, genomeId=None):
        genomeFile = self.get_genome_file(genomeId)

        return openRef(genomeFile)

    def get_pseudo_autosomal_regions(self):
        pars_x = self.config.get("PARs", "regions.X")
        pars_y = self.config.get("PARs", "regions.Y")

        regions_x = []
        regions_y = []
        for reg in pars_x.split(','):
            r = Region.from_str(reg.strip())
            regions_x.append(r)

        for reg in pars_y.split(','):
            r = Region.from_str(reg.strip())
            regions_y.append(r)

        return regions_x, regions_y

    def get_pars_x_test(self):
        regions_x, _ = self.get_pseudo_autosomal_regions()
        return lambda chrom, pos: any([r.isin(chrom, pos) for r in regions_x])

    def get_pars_y_test(self):
        _, regions_y = self.get_pseudo_autosomal_regions()
        return lambda chrom, pos: any([r.isin(chrom, pos) for r in regions_y])

    def get_gene_models(self, geneModelId=None, genomeId=None):
        if not genomeId:
            genomeId = self.defaultGenome
        if not geneModelId:
            geneModelId = self.config.get(
                'genome.' + genomeId, 'defaultGeneModel')
        key = genomeId + geneModelId
        if key not in self._geneModels:
            geneModelFile = self.config.get(
                'genome.' + genomeId, 'geneModel.' + geneModelId + '.file')
            gmDb = load_gene_models(geneModelFile)
            self._geneModels[key] = gmDb
        return self._geneModels[key]

    def get_mito_genome(self, mitoGenomeId=None):
        if not mitoGenomeId:
            mitoGenomeId = self.config.get(
                'mito_genomes', 'defaultMitoGenome')
        mitoGenomeFile = self.config.get(
            'mito_genome.' + mitoGenomeId, 'chrAllFile')
        return openRef(mitoGenomeFile)

    def get_mt_gene_models(self, mitoGeneModelId=None, mitoGenomeId=None):
        if not mitoGenomeId:
            mitoGenomeId = self.config.get('mito_genomes', 'defaultMitoGenome')
        if not mitoGeneModelId:
            mitoGeneModelId = self.config.get(
                'mito_genome.' + mitoGenomeId, 'defaultGeneModel')
        key = mitoGenomeId + mitoGeneModelId
        if key not in self._mitoGeneModels:
            mitoGeneModelFile = self.config.get(
                'mito_genome.' + mitoGenomeId,
                'geneModel.' + mitoGeneModelId + '.file')
            mmDb = load_gene_models(mitoGeneModelFile)
            self._mitoGeneModels[key] = mmDb
        return self._mitoGeneModels[key]


# GA = genomesDB.get_GA()
# GA = genomesDB.getGA("hg19")
