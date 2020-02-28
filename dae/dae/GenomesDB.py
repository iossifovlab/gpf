from dae.RegionOperations import Region
from dae.GenomeAccess import openRef
from dae.GeneModelFiles import load_gene_models

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.genomes_db import genomes_db_conf

"""
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
"""


class GenomesDB(object):
    def __init__(self, dae_dir, conf_file=None):
        self.dae_dir = dae_dir
        if not conf_file:
            conf_file = dae_dir + "/genomesDB.conf"

        self.config = GPFConfigParser.load_config(conf_file, genomes_db_conf)

        regions_x = [
            Region.from_str(region) for region in self.config.PARs.regions.X
        ]
        regions_y = [
            Region.from_str(region) for region in self.config.PARs.regions.Y
        ]
        regions = {"X": regions_x, "Y": regions_y}

        self.config = GPFConfigParser.modify_tuple(
            self.config,
            {
                "PARs": GPFConfigParser.modify_tuple(
                    self.config.PARs, {"regions": regions}
                )
            },
        )

        self.default_genome = self.config.genomes.default_genome
        self._gene_models = {}
        self._mito_gene_models = {}

    def get_genome_file(self, genome_id=None):
        if not genome_id:
            genome_id = self.default_genome
        genome_file = getattr(self.config.genome, genome_id).chr_all_file
        return genome_file

    def get_gene_model_id(self, genome_id=None):
        if not genome_id:
            genome_id = self.default_genome
        gene_model_id = getattr(
            self.config.genome, genome_id
        ).default_gene_model

        return gene_model_id

    def get_genome(self, genome_id=None):
        genome_file = self.get_genome_file(genome_id)
        genome = self.get_genome_from_file(genome_file)
        genome.pseudo_autosomal_regions = self.config.PARs.regions

        return genome

    def get_genome_from_file(self, genome_file=None):
        if genome_file is None:
            genome_file = self.get_genome_file()

        return openRef(genome_file)

    def get_gene_model(self, gene_model_id, genome_id):
        genome = getattr(self.config.genome, genome_id)
        gene_model = getattr(genome.gene_model, gene_model_id)
        return load_gene_models(gene_model.file)

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
            gene_model_id = self.get_gene_model_id(genome_id)

        key = genome_id + gene_model_id
        if key not in self._gene_models:
            gene_model = self.get_gene_model(gene_model_id, genome_id)
            self._gene_models[key] = gene_model

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
            mito_gene_model_id = self.config.mito_genome[
                mito_genome_id
            ].default_gene_model
        key = mito_genome_id + mito_gene_model_id
        if key not in self._mito_gene_models:
            mito_gene_model_file = (
                self.config.mito_genome[mito_genome_id]
                .gene_model[mito_gene_model_id]
                .file
            )
            mmDb = load_gene_models(mito_gene_model_file)
            self._mito_gene_models[key] = mmDb
        return self._mito_gene_models[key]
