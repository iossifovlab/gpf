from dae.GenomesDB import GenomesDB

from dae.configuration.configuration import DAEConfig

dae_config = DAEConfig.read_and_parse_file_configuration()

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_db.confFile)
