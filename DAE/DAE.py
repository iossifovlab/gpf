from GenomesDB import GenomesDB

from configurable_entities.configuration import DAEConfig

dae_config = DAEConfig()

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_conf)
