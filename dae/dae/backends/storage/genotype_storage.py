class GenotypeStorage:
    """Base class for genotype storages."""

    def __init__(self, storage_config, section_id):
        self.storage_config = storage_config
        self.id = section_id

    def is_impala(self):
        return False

    def is_filestorage(self):
        return False

    def build_backend(self, study_id, genome, gene_models):
        raise NotImplementedError()

    def simple_study_import(
        self,
        study_id,
        families_loader=None,
        variant_loaders=None,
        study_config=None,
        **kwargs,
    ):
        raise NotImplementedError()
