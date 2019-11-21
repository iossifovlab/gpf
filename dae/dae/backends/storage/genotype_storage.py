class GenotypeStorage:

    def __init__(self, storage_config):
        self.storage_config = storage_config
        self.id = self.storage_config.id

    def is_impala(self):
        return False

    def is_filestorage(self):
        return False

    def build_backend(self, study_id, genomes_db):
        raise NotImplementedError()
