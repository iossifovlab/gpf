from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
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
        browser_cache_path: Path | None = None,
    ) -> None:
        self._study_configs: dict[str, dict] = {}
        self.browser_cache_path = browser_cache_path
        self._cache: dict[str, PhenotypeData] = {}
        self._storage_registry = storage_registry
        if self.browser_cache_path is not None:
            self.browser_cache_path.mkdir(parents=True, exist_ok=True)
        if configurations is not None:
            for configuration in configurations:
                try:
                    self.register_study_config(configuration)
                except ValueError:
                    logger.exception(
                        "Failure while registering "
                        "phenotype study configuration",
                    )

    @staticmethod
    def load_configurations(pheno_data_dir: str) -> list[dict]:
        config_files = GPFConfigParser.collect_directory_configs(
            pheno_data_dir,
        )

        return [
            GPFConfigParser.load_config_dict(file, pheno_conf_schema)
            for file in config_files
        ]

    def register_study_config(
        self, study_config: dict, *, lock: bool = True,
    ) -> None:
        """Register a configuration as a loadable phenotype data."""
        if not study_config["enabled"]:
            return

        study_id = study_config["id"]
        storage_config = study_config.get("phenotype_storage")
        if storage_config is not None:
            storage_id = study_config["phenotype_storage"]["id"]
            if storage_id not in self._storage_registry:
                raise ValueError(
                    f"Cannot register '{study_id}', storage '{storage_id}' "
                    "not present in storage registry!",
                )
        if lock:
            with self.CACHE_LOCK:
                self._study_configs[study_config["id"]] = study_config

        self._study_configs[study_config["id"]] = study_config

    def has_phenotype_data(self, data_id: str, *, lock: bool = True) -> bool:
        if lock:
            with self.CACHE_LOCK:
                return data_id in self._study_configs
        else:
            return data_id in self._study_configs

    def get_phenotype_data_config(self, data_id: str) -> dict | None:
        with self.CACHE_LOCK:
            return self._study_configs[data_id]

    def get_phenotype_data_ids(self, *, lock: bool = True) -> list[str]:
        if lock:
            with self.CACHE_LOCK:
                return list(self._study_configs.keys())
        return list(self._study_configs.keys())

    def get_phenotype_data(
        self, data_id: str, *, lock: bool = True,
    ) -> PhenotypeData:
        """
        Return an instance of phenotype data from the registry.

        If the phenotype data hasn't been loaded it, load and cache.
        """
        return self._get_or_load(data_id, lock=lock)

    def get_all_phenotype_data(
        self, *, lock: bool = True,
    ) -> list[PhenotypeData]:
        """Return all registered phenotype data."""
        return [
            self._get_or_load(pheno_id, lock=lock)
            for pheno_id in self._study_configs
        ]

    def _get_or_load(
        self,
        pheno_id: str,
        *,
        lock: bool = True,
    ) -> PhenotypeData:
        """Return a phenotype data from the cache and load it if necessary."""
        if lock:
            with self.CACHE_LOCK:
                if pheno_id in self._cache:
                    return self._cache[pheno_id]
                return self._load(pheno_id)
        if pheno_id in self._cache:
            return self._cache[pheno_id]
        return self._load(pheno_id)

    def _load(self, pheno_id: str):
        config = self._study_configs[pheno_id]

        if config["type"] == "study":
            pheno_data = self._load_study(config)
        elif config["type"] == "group":
            pheno_data = self._load_group(config)
        else:
            raise ValueError(f"Invalid type '{config['type']}'"
                                f" in config for {pheno_id}")

        cache_path = self._make_cache_path_for(config)
        pheno_data.cache_path = cache_path
        return pheno_data

    def _make_cache_path_for(self, study_config: dict) -> Path | None:
        if self.browser_cache_path is None:
            return None

        path = self.browser_cache_path / study_config["id"]
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _load_study(self, study_config: dict) -> PhenotypeData:
        pheno_id = study_config["id"]
        study_storage_config = study_config.get("phenotype_storage")
        if study_storage_config is not None:
            study_storage_id = study_storage_config["id"]
            study_storage = self._storage_registry.get_phenotype_storage(
                study_storage_id,
            )
        else:
            study_storage = \
                self._storage_registry.get_default_phenotype_storage()

        self._cache[pheno_id] = study_storage.build_phenotype_study(
            study_config, browser_cache_path=self.browser_cache_path)

        return self._cache[pheno_id]

    def _load_group(self, study_config: dict) -> PhenotypeData:
        pheno_id = study_config["id"]
        missing_children = set(study_config["children"]).difference(
            set(self._study_configs),
        )
        if len(missing_children) > 0:
            raise ValueError(
                f"Cannot load group {pheno_id}; the following child studies "
                f"{missing_children} are not registered",
            )
        children = [
            self._get_or_load(child_id, lock=False)
            for child_id in study_config["children"]
        ]
        self._cache[pheno_id] = PhenotypeGroup(
            pheno_id, study_config, children,
            cache_path=self.browser_cache_path,
        )
        return self._cache[pheno_id]

    def shutdown(self) -> None:
        """Shutdown the registry and all loaded phenotype data."""
        with self.CACHE_LOCK:
            for pheno_data in self._cache.values():
                pheno_data.close()
