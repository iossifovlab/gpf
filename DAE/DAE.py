from __future__ import print_function, absolute_import
from __future__ import unicode_literals

from GenomesDB import GenomesDB

from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb
from pheno.pheno_factory import PhenoFactory

dae_config = DAEConfig()

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_conf)
pheno_factory = PhenoFactory(dae_config)

variants_db = VariantsDb(dae_config, pheno_factory=pheno_factory)
