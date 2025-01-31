from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from dae.pheno.pheno_data import PhenotypeStudy

logger = logging.getLogger(__name__)


class PhenotypeStorage:
    """Class that manages phenotype data storage directories."""
    def __init__(self, storage_config: dict[str, Any]):
        self.config = storage_config
        self.storage_id = self.config["id"]
        self.base_dir = Path(self.config["base_dir"])

    @staticmethod
    def from_config(storage_config: dict[str, Any]) -> PhenotypeStorage:
        return PhenotypeStorage(storage_config)

    def build_phenotype_study(
        self, study_config: dict,
        browser_cache_path: Path | None,
    ) -> PhenotypeStudy:
        """Create a phenotype study object from a configuration."""
        study_id = study_config["name"]
        study_storage_config = study_config.get("phenotype_storage")
        if study_storage_config is not None:
            study_storage_id = study_storage_config["id"]
            if study_storage_id != self.storage_id:
                raise ValueError(
                    f"Attempted to create phenotype study {study_id}"
                    f"in storage {self.storage_id}; "
                    f"study config requests "
                    f"different storage {study_storage_id}",
                )

        dbfile: Path

        if study_storage_config is None or "db" not in study_storage_config:
            dbfile = self.base_dir / f"{study_id}/{study_id}.db"
        else:
            filename = study_config["phenotype_storage"]["db"]
            dbfile = self.base_dir / filename

        if not dbfile.exists():
            raise ValueError(
                f"Cannot find pheno study dbfile {dbfile} for {study_id} "
                f"in phenotype storage {self.storage_id}",
            )

        return PhenotypeStudy(
            study_id, str(dbfile), study_config,
            cache_path=browser_cache_path,
        )

    def shutdown(self) -> None:
        return


class PhenotypeStorageRegistry:
    """Class that manages phenotype storages."""
    def __init__(self) -> None:
        self._phenotype_storages: dict[str, PhenotypeStorage] = {}
        self._default_phenotype_storage: PhenotypeStorage | None = None

    def __contains__(self, key: str) -> bool:
        return key in self._phenotype_storages

    def register_storage_config(
            self, storage_config: dict[str, Any]) -> PhenotypeStorage:
        """Create a phenotype storage using storage config and registers it."""
        return self.register_phenotype_storage(
            PhenotypeStorage.from_config(storage_config),
        )

    def register_phenotype_storage(
            self, storage: PhenotypeStorage) -> PhenotypeStorage:
        """Register a phenotype storage instance."""
        storage_id = storage.storage_id
        self._phenotype_storages[storage_id] = storage
        return storage

    def register_default_storage(
            self, phenotype_storage: PhenotypeStorage) -> None:
        """Register a phenotype storage and make it the default storage."""
        self.register_phenotype_storage(phenotype_storage)
        self._default_phenotype_storage = phenotype_storage

    def get_default_phenotype_storage(self) -> PhenotypeStorage:
        """Return the default phenotype storage if one is defined.

        Otherwise, return None.
        """
        if self._default_phenotype_storage is None:
            raise ValueError("default phenotype storage not set")
        return self._default_phenotype_storage

    def get_phenotype_storage(self, storage_id: str) -> PhenotypeStorage:
        """Return phenotype storage with specified storage_id.

        If the method can not find storage with the specified ID, it will raise
        ValueError exception.
        """
        if storage_id not in self._phenotype_storages:
            raise ValueError(f"unknown storage id: <{storage_id}>")
        return self._phenotype_storages[storage_id]

    def get_all_phenotype_storage_ids(self) -> list[str]:
        """Return list of all registered phenotype storage IDs."""
        return list(self._phenotype_storages.keys())

    def get_all_phenotype_storages(self) -> list[PhenotypeStorage]:
        """Return list of registered phenotype storages."""
        return list(self._phenotype_storages.values())

    def register_storages_configs(
            self, phenotype_storages_config: dict[str, Any]) -> None:
        """Create and register all phenotype storages defined in config.

        When defining a GPF instance, we specify a `phenotype_storage` section
        in the configuration. If you pass this whole configuration section
        to this method, it will create and register all phenotype storages
        defined in that configuration section.
        """
        for storage_config in phenotype_storages_config["storages"]:
            self.register_storage_config(storage_config)
        default_storage_id = phenotype_storages_config.get("default")
        if default_storage_id is not None:
            storage = self.get_phenotype_storage(default_storage_id)
            self.register_default_storage(storage)

    def shutdown(self) -> None:
        for storage_id, storage in self._phenotype_storages.items():
            logger.info("shutting down phenotype storage %s", storage_id)
            storage.shutdown()
