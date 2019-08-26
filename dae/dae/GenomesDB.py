from dae.GenomeAccess import openRef
from dae.GeneModelFiles import load_gene_models

from dae.genomes_config_parser import GenomesConfigParser

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

    def __init__(self, dae_dir, conf_file=None):
        self.dae_dir = dae_dir
        if not conf_file:
            conf_file = dae_dir + '/genomesDB.conf'

        self.config = GenomesConfigParser.read_and_parse_file_configuration(
            conf_file, dae_dir)

        self.default_genome = self.config.genomes.default_genome
        self._gene_models = {}
        self._mito_gene_models = {}

    def get_genome_file(self, genome_id=None):
        if not genome_id:
            genome_id = self.default_genome
        genome_file = self.config.genome[genome_id].chr_all_file
        return genome_file

    def get_genome(self, genome_id=None):
        genome_file = self.get_genome_file(genome_id)

        return openRef(genome_file)

    def get_pars_x_test(self):
        regions_x = self.config.PARs.regions.x.region
        return lambda chrom, pos: any([r.isin(chrom, pos) for r in regions_x])

    def get_pars_y_test(self):
        regions_y = self.config.PARs.regions.y.region
        return lambda chrom, pos: any([r.isin(chrom, pos) for r in regions_y])

    def get_gene_models(self, gene_model_id=None, genome_id=None):
        if not genome_id:
            genome_id = self.default_genome
        if not gene_model_id:
            gene_model_id = self.config.genome[genome_id].default_gene_model
        key = genome_id + gene_model_id
        if key not in self._gene_models:
            gene_model_file = \
                self.config.genome[genome_id].gene_model[gene_model_id].file
            gmDb = load_gene_models(gene_model_file)
            self._gene_models[key] = gmDb
        return self._gene_models[key]

    def get_mito_genome(self, mito_genome_id=None):
        if not mito_genome_id:
            mito_genome_id = self.config.mito_genomes.default_mito_genome
        mito_genome_file = self.config.mito_genome[mito_genome_id].chr_all_file
        return openRef(mito_genome_file)

    def get_mt_gene_models(self, mito_gene_model_id=None, mito_genome_id=None):
        if not mito_genome_id:
            mito_genome_id = self.config.mito_genomes.default_mito_genome
        if not mito_gene_model_id:
            mito_gene_model_id = \
                self.config.mito_genome[mito_genome_id].default_gene_model
        key = mito_genome_id + mito_gene_model_id
        if key not in self._mito_gene_models:
            mito_gene_model_file = self.config.mito_genome[mito_genome_id]. \
                gene_model[mito_gene_model_id].file
            mmDb = load_gene_models(mito_gene_model_file)
            self._mito_gene_models[key] = mmDb
        return self._mito_gene_models[key]
