class GenotypeStorage:
    def __init__(self, storage_config):
        print(storage_config)
        self.storage_config = storage_config
        self.id = self.storage_config.section_id()

    def is_impala(self):
        return False

    def is_filestorage(self):
        return False

    def build_backend(self, study_id, genomes_db):
        raise NotImplementedError()

    def simple_study_import(
        self, study_id, families_loader=None, variant_loaders=None, **kwargs
    ):
        raise NotImplementedError()
