import logging
from typing import cast

from dae.genotype_storage import get_genotype_storage_factory
from dae.genotype_storage.genotype_storage import GenotypeStorage

logger = logging.getLogger(__name__)


class GenotypeStorageRegistry:
    """Create the correct Genotype Storage."""

    def __init__(self):
        self._genotype_storages = {}
        self._default_genotype_storage: GenotypeStorage = None

    def register_genotype_storage(self, storage_config) -> GenotypeStorage:
        """Create a genotype storage by storage config and registers it."""
        storage_id = storage_config["id"]
        storage_type = storage_config["storage_type"]
        storage_factory = get_genotype_storage_factory(storage_type)

        genotype_storage = storage_factory(storage_config)
        self._genotype_storages[storage_id] = genotype_storage
        return genotype_storage

    def register_default_storage(self, genotype_storage):
        self._default_genotype_storage = genotype_storage

    def get_default_genotype_storage(self) -> GenotypeStorage:
        return self._default_genotype_storage

    def get_genotype_storage(self, storage_id) -> GenotypeStorage:
        """Create and return a genotype storage with id genotype_storage_id."""
        if storage_id not in self._genotype_storages:
            raise ValueError(f"unknown storage id {storage_id}")
        return cast(GenotypeStorage, self._genotype_storages[storage_id])

    def get_genotype_storage_ids(self):
        return list(self._genotype_storages.keys())

    def register_storages_config(self, genotype_storages_config):
        for storage_config in genotype_storages_config["storages"]:
            self.register_genotype_storage(storage_config)
        default_storage_id = genotype_storages_config.default
        if default_storage_id is not None:
            storage = self.get_genotype_storage(default_storage_id)
            self.register_default_storage(storage)

    def shutdown(self):
        for storage_id, storage in self._genotype_storages.items():
            logger.info("shutting down genotype storage %s", storage_id)
            storage.shutdown()
