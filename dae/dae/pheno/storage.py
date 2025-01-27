from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PhenotypeStorage:
    def __init__(self, storage_config: dict[str, Any]):
        self.config = storage_config
        self.storage_id = self.config["id"]

    @staticmethod
    def from_config(storage_config: dict[str, Any]) -> PhenotypeStorage:
        return PhenotypeStorage(storage_config)

    def shutdown(self):
        pass


class PhenoStorageRegistry:
    def __init__(self) -> None:
        self._phenotype_storages: dict[str, PhenotypeStorage] = {}
        self._default_phenotype_storage: PhenotypeStorage | None = None

    def register_storage_config(
            self, storage_config: dict[str, Any]) -> PhenotypeStorage:
        """Create a genotype storage using storage config and registers it."""
        return self.register_phenotype_storage(
            PhenotypeStorage.from_config(storage_config),
        )

    def register_phenotype_storage(
            self, storage: PhenotypeStorage) -> PhenotypeStorage:
        """Register a genotype storage instance."""
        storage_id = storage.storage_id
        self._phenotype_storages[storage_id] = storage
        return storage

    def register_default_storage(
            self, phenotype_storage: PhenotypeStorage) -> None:
        """Register a genotype storage and make it the default storage."""
        self.register_phenotype_storage(phenotype_storage)
        self._default_phenotype_storage = phenotype_storage

    def get_default_genotype_storage(self) -> PhenotypeStorage:
        """Return the default genotype storage if one is defined.

        Otherwise, return None.
        """
        if self._default_phenotype_storage is None:
            raise ValueError("default genotype storage not set")
        return self._default_phenotype_storage

    def get_genotype_storage(self, storage_id: str) -> PhenotypeStorage:
        """Return genotype storage with specified storage_id.

        If the method can not find storage with the specified ID, it will raise
        ValueError exception.
        """
        if storage_id not in self._phenotype_storages:
            raise ValueError(f"unknown storage id: <{storage_id}>")
        return self._phenotype_storages[storage_id]

    def get_all_genotype_storage_ids(self) -> list[str]:
        """Return list of all registered genotype storage IDs."""
        return list(self._phenotype_storages.keys())

    def get_all_genotype_storages(self) -> list[PhenotypeStorage]:
        """Return list of registered genotype storages."""
        return list(self._phenotype_storages.values())

    def register_storages_configs(
            self, genotype_storages_config: dict[str, Any]) -> None:
        """Create and register all genotype storages defined in config.

        When defining a GPF instance, we specify a `genotype_storage` section
        in the configuration. If you pass this whole configuration section
        to this method, it will create and register all genotype storages
        defined in that configuration section.
        """
        for storage_config in genotype_storages_config["storages"]:
            self.register_storage_config(storage_config)
        default_storage_id = genotype_storages_config.get("default")
        if default_storage_id is not None:
            storage = self.get_genotype_storage(default_storage_id)
            self.register_default_storage(storage)

    def shutdown(self) -> None:
        for storage_id, storage in self._phenotype_storages.items():
            logger.info("shutting down genotype storage %s", storage_id)
            storage.shutdown()
