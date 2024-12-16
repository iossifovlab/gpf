from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import Any, cast

from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.pheno.pheno_data import PhenotypeData, load_phenotype_data

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

        configurations: dict[str, Box] = {}
        groups: list[str] = []

        with PhenoRegistry.CACHE_LOCK:
            for config_path in pheno_configs:
                logger.info(
                    "loading phenotype data from config: %s", config_path,
                )
                config = GPFConfigParser.load_config(
                    str(config_path), pheno_conf_schema,
                )
                pheno_id = config["name"]
                configurations[pheno_id] = config
                if config["type"] == "group":
                    groups.append(pheno_id)
                    continue
                registry.register_phenotype_data(
                    load_phenotype_data(config),
                    lock=False,
                )
            for group in groups:
                group_config = configurations[group]
                registry.register_phenotype_data(
                    load_phenotype_data(
                        group_config,
                        cast(list[dict[str, Any]], configurations.values()),
                    ),
                    lock=False,
                )

        return registry
