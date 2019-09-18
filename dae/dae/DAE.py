from dae.GenomesDB import GenomesDB

from dae.gpf_instance.gpf_instance import GPFInstance

gpf_instance = GPFInstance()
dae_config = gpf_instance.dae_config

genomesDB = GenomesDB(dae_config.dae_data_dir, dae_config.genomes_db.confFile)
