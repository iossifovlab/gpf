import abc
from deprecation import deprecated


class GenotypeStorage(abc.ABC):
    """Base class for genotype storages."""

    def __init__(self, storage_config, storage_id):
        self.storage_config = storage_config
        self.storage_id = storage_id

    @property  # type: ignore
    @deprecated(details="switch to using storage_id")
    def id(self):
        return self.storage_id

    @deprecated(details="pending remove from the API")
    def is_impala(self):  # pylint: disable=no-self-use
        return False

    @deprecated(details="pending remove from the API")
    def is_filestorage(self):  # pylint: disable=no-self-use
        return False

    @abc.abstractmethod
    def build_backend(self, study_config, genome, gene_models):
        raise NotImplementedError()

    @abc.abstractmethod
    def simple_study_import(
            self,
            study_id,
            families_loader=None,
            variant_loaders=None,
            study_config=None,
            **kwargs):
        """Handle import of simple studies."""
        raise NotImplementedError()
