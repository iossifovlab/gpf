from collections import namedtuple
from typing import List


from dae.utils.regions import Region
from dae.genome.genome_access import open_ref
from dae.genome.gene_models import load_gene_models

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


class Genome:
    def __init__(self, genome_id):
        assert genome_id is not None

        self.genome_id = genome_id
        self._gene_models = {}
        self.default_gene_models_id = None
        self.pars = {}
        self.genomic_sequence_filename = None
        self.genomic_sequence = None

    GeneModelsConfig = namedtuple(
        "GeneModelConfig", ["id", "filename", "fileformat", "gene_models"]
    )

    @staticmethod
    def load_config(genome_config):
        genome = Genome(genome_config.section_id())

        genome.genomic_sequence_filename = genome_config.chr_all_file

        for gene_models_config in genome_config.gene_models:
            gene_models = Genome.GeneModelsConfig(
                gene_models_config.section_id(),
                gene_models_config.file,
                gene_models_config.fileformat,
                None,
            )
            genome._gene_models[gene_models.id] = gene_models

        assert genome_config.default_gene_models in genome._gene_models
        genome.default_gene_models_id = genome_config.default_gene_models

        if genome_config.pars:
            assert genome_config.pars.X is not None
            regions_x = [
                Region.from_str(region) for region in genome_config.pars.X
            ]
            chrom_x = regions_x[0].chrom

            regions_y = [
                Region.from_str(region) for region in genome_config.pars.Y
            ]
            chrom_y = regions_y[0].chrom
            genome.pars = {chrom_x: regions_x, chrom_y: regions_y}

        return genome

    def get_genomic_sequence(self):
        if self.genomic_sequence is None:
            self.genomic_sequence = open_ref(self.genomic_sequence_filename)
        return self.genomic_sequence

    def get_gene_models(self, gene_models_id=None):
        if gene_models_id is None:
            gene_models_id = self.default_gene_models_id
        gene_models_config = self._gene_models[gene_models_id]
        if gene_models_config.gene_models is None:
            gene_models = load_gene_models(
                gene_models_config.filename, gene_models_config.fileformat
            )
            gene_models_config = self.GeneModelsConfig(
                gene_models_id,
                gene_models_config.filename,
                gene_models_config.fileformat,
                gene_models,
            )
            self._gene_models[gene_models_id] = gene_models_config
        return gene_models_config.gene_models

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        # TODO Handle variants which are both inside and outside a PARs
        # Currently, if the position of the reference is within a PAR,
        # the whole variant is considered to be within an autosomal region
        def in_any_region(chrom: str, pos: int, regions: List[Region]) -> bool:
            return any(map(lambda reg: reg.isin(chrom, pos), regions))

        pars_regions = self.pars.get(chrom, None)
        if pars_regions:
            return in_any_region(
                chrom, pos, pars_regions  # type: ignore
            )
        else:
            return False


class GenomesDB(object):
    def __init__(self, dae_dir, conf_file=None):
        self.dae_dir = dae_dir
        if not conf_file:
            conf_file = f"{dae_dir}/genomesDB.conf"

        self.config = GPFConfigParser.load_config(conf_file, genomes_db_conf)

        self._genomes = {}

        for genome_config in self.config.genome:
            genome = Genome.load_config(genome_config)
            assert genome is not None
            self._genomes[genome.genome_id] = genome

        assert self.config.genomes.default_genome in self._genomes
        self.default_genome = self._genomes[self.config.genomes.default_genome]

    def get_genome(self, genome_id=None):
        if genome_id is None:
            genome = self.default_genome
        else:
            genome = self._genomes[genome_id]
        return genome

    def get_genomic_sequence_filename(self, genome_id=None):
        genome = self.get_genome(genome_id)
        return genome.genomic_sequence_filename

    def get_genomic_sequence(self, genome_id=None):
        genome = self.get_genome(genome_id)
        return genome.get_genomic_sequence()

    def get_default_gene_models_id(self, genome_id=None):
        genome = self.get_genome(genome_id)
        return genome.default_gene_model_id

    def get_gene_models(self, gene_model_id=None, genome_id=None):
        genome = self.get_genome(genome_id)
        gene_model = genome.get_gene_models(gene_model_id)
        return gene_model

    def load_genomic_sequence(self, genomic_sequence_filename=None):
        if genomic_sequence_filename is None:
            return self.default_genome.get_genomic_sequence()

        return open_ref(genomic_sequence_filename)

    def load_gene_models(
        self, gene_models_file=None, gene_models_fileformat=None
    ):
        if gene_models_file is None:
            return self.default_genome.get_gene_models()

        from dae.genome import gene_models

        return gene_models.load_gene_models(
            gene_models_file, gene_models_fileformat
        )
