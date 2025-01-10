from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.pheno.pheno_data import PhenotypeData, PhenotypeGroup, PhenotypeStudy

logger = logging.getLogger(__name__)


class PhenoRegistry:
    """Class to register phenotype data."""

    CACHE_LOCK = Lock()

    def __init__(self) -> None:
        self._cache: dict[str, PhenotypeData] = {}

    def _register_study(self, study: PhenotypeData) -> None:
        if study.pheno_id in self._cache:
            raise ValueError(
                f"Pheno ID {study.pheno_id} already loaded.",
            )

        self._cache[study.pheno_id] = study

    def register_phenotype_data(
        self, phenotype_data: PhenotypeData, *, lock: bool = True,
    ) -> None:
        """Register a phenotype data study."""
        if lock:
            with self.CACHE_LOCK:
                self._register_study(phenotype_data)
        else:
            self._register_study(phenotype_data)

    def has_phenotype_data(self, data_id: str) -> bool:
        with self.CACHE_LOCK:
            return data_id in self._cache

    def get_phenotype_data(self, data_id: str) -> PhenotypeData:
        with self.CACHE_LOCK:
            return self._cache[data_id]

    def get_phenotype_data_config(self, data_id: str) -> Box | None:
        with self.CACHE_LOCK:
            return self._cache[data_id].config

    def get_phenotype_data_ids(self) -> list[str]:
        return list(self._cache.keys())

    def get_all_phenotype_data(self) -> list[PhenotypeData]:
        return list(self._cache.values())

    def get_or_load(
        self,
        pheno_id: str,
        pheno_configurations: dict[str, dict],
    ) -> PhenotypeData:
        """Return a phenotype data from the cache and load it if necessary."""
        if pheno_id in self._cache:
            return self._cache[pheno_id]

        config = pheno_configurations[pheno_id]

        if config["type"] == "study":
            study = PhenotypeStudy(config["name"], config["dbfile"], config)
            self.register_phenotype_data(study, lock=False)
            return self._cache[pheno_id]

        if config["type"] == "group":
            children = [self.get_or_load(child, pheno_configurations)
                        for child in config["children"]]
            group = PhenotypeGroup(config["name"], config, children)
            self.register_phenotype_data(group, lock=False)
            return self._cache[pheno_id]

        raise ValueError(f"Invalid type '{config['type']}'"
                            f" in config for {pheno_id}")

    @staticmethod
    def from_directory(pheno_data_dir: Path) -> PhenoRegistry:
        """Create a registry with all phenotype studies in a directory."""
        registry = PhenoRegistry()
        logger.info("pheno registry created: %s", id(registry))
        pheno_configs = [
            Path(c) for c in
            GPFConfigParser.collect_directory_configs(
                str(pheno_data_dir),
            )
        ]

        configurations: dict[str, dict] = {}

        with PhenoRegistry.CACHE_LOCK:
            for conf_path in pheno_configs:
                logger.info("collecting phenotype data config: %s", conf_path)
                config = GPFConfigParser.load_config(
                    str(conf_path), pheno_conf_schema)
                configurations[config["name"]] = config

            for pheno_id in configurations:
                logger.info("loading phenotype data config: %s", pheno_id)
                registry.get_or_load(pheno_id, configurations)

        return registry
