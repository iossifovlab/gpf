import logging
from typing import Dict

from dae.genotype_storage import get_genotype_storage_factory
from dae.genotype_storage.genotype_storage import GenotypeStorage

logger = logging.getLogger(__name__)


class GenotypeStorageRegistry:
    """Registry for genotype storages.

    This class could accept genotype storages config from a GPF instance
    configuration and instantiate and register all genotype storages defined
    in this configuration. To do this, one could use
    :meth:`GenotypeStorageRegistry.register_storages_configs`.

    To create and register single genotype storage using its configuration
    you can use :meth:`GenotypeStorageRegistry.register_storage_config`.

    When you have already created an instance of genotype storage, you can use
    :meth:`GenotypeStorageRegistry.register_genotype_storage` to register
    it.
    """

    def __init__(self):
        self._genotype_storages: Dict[str, GenotypeStorage] = {}
        self._default_genotype_storage: GenotypeStorage = None

    def register_storage_config(
            self, storage_config) -> GenotypeStorage:
        """Create a genotype storage using storage config and registers it."""
        storage_type = storage_config["storage_type"]
        storage_factory = get_genotype_storage_factory(storage_type)

        genotype_storage = storage_factory(storage_config)
        return self.register_genotype_storage(genotype_storage)

    def register_genotype_storage(
            self, storage: GenotypeStorage) -> GenotypeStorage:
        """Register a genotype storage instance."""
        if not isinstance(storage, GenotypeStorage):
            raise ValueError(
                f"trying to register object of type <{type(storage)}>"
                f" as genotype storage.")
        storage_id = storage.storage_id
        self._genotype_storages[storage_id] = storage
        return storage

    def register_default_storage(self, genotype_storage):
        """Register a genotype storage and make it the default storage."""
        self.register_genotype_storage(genotype_storage)
        self._default_genotype_storage = genotype_storage

    def get_default_genotype_storage(self) -> GenotypeStorage:
        """Return the default genotype storage if one is defined.

        Otherwise, return None.
        """
        if self._default_genotype_storage is None:
            raise ValueError("default genotype storage not set")
        return self._default_genotype_storage

    def get_genotype_storage(self, storage_id) -> GenotypeStorage:
        """Return genotype storage with specified storage_id.

        If the method can not find storage with the specified ID, it will raise
        ValueError exception.
        """
        if storage_id is None:
            return self.get_default_genotype_storage()
        if storage_id not in self._genotype_storages:
            raise ValueError(f"unknown storage id {storage_id}")
        return self._genotype_storages[storage_id]

    def get_all_genotype_storage_ids(self):
        """Return list of all registered genotype storage IDs."""
        return list(self._genotype_storages.keys())

    def get_all_genotype_storages(self):
        """Return list of registered genotype storages."""
        return list(self._genotype_storages.values())

    def register_storages_configs(self, genotype_storages_config):
        """Create and register all genotype storages defined in config.

        When defining a GPF instance, we specify a `genotype_storage` section
        in the configuration. If you pass this whole configuration section
        to this method, it will create and register all genotype storages
        defined in that configuration section.
        """
        for storage_config in genotype_storages_config["storages"]:
            self.register_storage_config(storage_config)
        default_storage_id = genotype_storages_config.default
        if default_storage_id is not None:
            storage = self.get_genotype_storage(default_storage_id)
            self.register_default_storage(storage)

    def shutdown(self):
        for storage_id, storage in self._genotype_storages.items():
            logger.info("shutting down genotype storage %s", storage_id)
            storage.shutdown()
