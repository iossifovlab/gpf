class GenotypeStorage:
    """Base class for genotype storages."""

    def __init__(self, storage_config, section_id):
        self.storage_config = storage_config
        self.id = section_id  # pylint: disable=invalid-name

    def is_impala(self):  # pylint: disable=no-self-use
        """Return True if this is an impala storage."""
        return False

    def is_filestorage(self):  # pylint: disable=no-self-use
        """Return True if this is a file storage."""
        return False

    def build_backend(self, study_config, genome, gene_models):
        raise NotImplementedError()

    def simple_study_import(
        self,
        study_id,
        families_loader=None,
        variant_loaders=None,
        study_config=None,
        **kwargs,
    ):
        """Import simple study."""
        raise NotImplementedError()
