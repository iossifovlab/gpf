from __future__ import print_function, absolute_import
from __future__ import unicode_literals

from GenomesDB import GenomesDB

from configurable_entities.configuration import DAEConfig

dae_config = DAEConfig.make_config()

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_conf)
