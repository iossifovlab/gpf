from __future__ import annotations

import logging
from threading import Lock

from box import Box

from dae.pheno.pheno_data import PhenotypeData, PhenotypeGroup
from dae.pheno.storage import PhenotypeStorageRegistry

logger = logging.getLogger(__name__)


class PhenoRegistry:
    """
    Class for managing runtime instances of phenotype data.

    Requires a PhenotypeStorageRegistry to function.

    The registry has 2 main operations, register and get.
    Registering requires a study configuration and makes the registry
    aware of a phenotype study's existence, making it loadable.

    Getting a phenotype data requires the ID and
    will perform a load if necessary.

    Both operations are synchronized and use a mutex to prevent faulty reads
    or duplicate loads of a phenotype data.
    """

    CACHE_LOCK = Lock()

    def __init__(
        self, storage_registry: PhenotypeStorageRegistry,
        configurations: list[dict] | None = None,
    ) -> None:
        self._study_configs: dict[str, dict] = {}
        self._cache: dict[str, PhenotypeData] = {}
        self._storage_registry = storage_registry
        if configurations is not None:
            for configuration in configurations:
                try:
                    self.register_study_config(configuration)
                except ValueError:
                    logger.exception(
                        "Failure while registering "
                        "phenotype study configuration",
                    )

    def register_study_config(
        self, study_config: dict, *, lock: bool = True,
    ) -> None:
        """Register a configuration as a loadable phenotype data."""
        study_id = study_config["name"]
        storage_id = study_config["phenotype_storage"]["id"]
        if storage_id not in self._storage_registry:
            raise ValueError(
                f"Cannot register '{study_id}', storage '{storage_id}' "
                "not present in storage registry!",
            )
        if lock:
            with self.CACHE_LOCK:
                self._study_configs[study_config["name"]] = study_config

        self._study_configs[study_config["name"]] = study_config

    def has_phenotype_data(self, data_id: str, *, lock: bool = True) -> bool:
        if lock:
            with self.CACHE_LOCK:
                return data_id in self._study_configs
        else:
            return data_id in self._study_configs

    def get_phenotype_data_config(self, data_id: str) -> Box | None:
        with self.CACHE_LOCK:
            return self._cache[data_id].config

    def get_phenotype_data_ids(self, *, lock: bool = True) -> list[str]:
        if lock:
            with self.CACHE_LOCK:
                return list(self._study_configs.keys())
        return list(self._study_configs.keys())

    def get_phenotype_data(
        self, data_id: str, *, lock: bool = True,
    ) -> PhenotypeData:
        """Return """
        if lock:
            with self.CACHE_LOCK:
                return self._get_or_load(data_id)
        else:
            return self._get_or_load(data_id)

    def get_all_phenotype_data(
        self, *, lock: bool = True,
    ) -> list[PhenotypeData]:
        """Return all registered phenotype data."""
        if lock:
            with self.CACHE_LOCK:
                return [
                    self._get_or_load(pheno_id)
                    for pheno_id in self._study_configs
                ]
        else:
            return [
                self._get_or_load(pheno_id) for pheno_id in self._study_configs
            ]

    def _get_or_load(
        self,
        pheno_id: str,
    ) -> PhenotypeData:
        """Return a phenotype data from the cache and load it if necessary."""
        if pheno_id in self._cache:
            return self._cache[pheno_id]

        config = self._study_configs[pheno_id]

        if config["type"] == "study":
            return self._load_study(config)

        if config["type"] == "group":
            return self._load_group(config)

        raise ValueError(f"Invalid type '{config['type']}'"
                            f" in config for {pheno_id}")

    def _load_study(self, study_config: dict) -> PhenotypeData:
        pheno_id = study_config["name"]
        study_storage_id = study_config.get("phenotype_storage")
        if study_storage_id is not None:
            study_storage = self._storage_registry.get_phenotype_storage(
                study_storage_id,
            )
        else:
            study_storage = \
                self._storage_registry.get_default_phenotype_storage()

        self._cache[pheno_id] = study_storage.build_phenotype_study(
            study_config)

        return self._cache[pheno_id]

    def _load_group(self, study_config: dict) -> PhenotypeData:
        pheno_id = study_config["name"]
        children = [
            self._get_or_load(child_id)
            for child_id in study_config["children"]
        ]
        self._cache[pheno_id] = PhenotypeGroup(
            pheno_id, study_config, children,
        )
        return self._cache[pheno_id]
