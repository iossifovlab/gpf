from __future__ import print_function, absolute_import
from __future__ import unicode_literals

from GeneInfoDB import GeneInfoDB
from GenomesDB import GenomesDB


from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb

# from pheno.pheno_factory import PhenoFactory

dae_config = DAEConfig()

giDB = GeneInfoDB(dae_config.gene_info_conf, dae_config.dae_data_dir)
genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_conf)

variants_db = VariantsDb(dae_config)
