from __future__ import print_function
from __future__ import unicode_literals

from GeneInfoDB import GeneInfoDB
from GenomesDB import GenomesDB


from configurable_entities.configuration import DAEConfig

# from pheno.pheno_factory import PhenoFactory

config = DAEConfig()

giDB = GeneInfoDB(config.gene_info_conf, config.dae_data_dir)
genomesDB = GenomesDB(config.dae_data_dir, config.genomes_conf)
