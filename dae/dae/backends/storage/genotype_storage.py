class GenotypeStorage:

    def __init__(self, storage_config):
        self.storage_config = storage_config

    def is_impala(self):
        return False

    def is_filestorage(self):
        return False

    def get_backend(self, study_config, genomes_db):
        raise NotImplementedError()
