from dae.GenomesDB import GenomesDB

from dae.configurable_entities.configuration import DAEConfig

dae_config = DAEConfig.make_config()

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_conf)
