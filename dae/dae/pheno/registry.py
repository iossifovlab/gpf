from __future__ import annotations

import logging
import pathlib
from threading import Lock

from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import (
    groups_file_schema,
    pheno_conf_schema,
)
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
        self, phenotype_data: PhenotypeData, lock: bool = True,
    ) -> None:
        """Register a phenotype data study."""
        if lock:
            with self.CACHE_LOCK:
                self._register_study(phenotype_data)
        else:
            self._register_study(phenotype_data)

    @classmethod
    def load_pheno_data(cls, path: pathlib.Path) -> PhenotypeData:
        """Create a PhenotypeStudy object from a configuration file."""
        if not path.is_file() or (
            not path.name.endswith(".yaml")
            and not path.name.endswith(".conf")
        ):
            raise ValueError("Invalid PhenotypeStudy path")
        config = GPFConfigParser.load_config(str(path), pheno_conf_schema)
        pheno_id = config["phenotype_data"]["name"]
        logger.info("creating phenotype data <%s>", pheno_id)
        return PhenotypeStudy(
            pheno_id,
            config["phenotype_data"]["dbfile"],
            config=config["phenotype_data"],
        )

    @classmethod
    def load_pheno_groups(
        cls, path: pathlib.Path,
        registry: PhenoRegistry,
    ) -> list[PhenotypeGroup]:
        """
        Load groups from groups file.

        Groups file should be a config file named 'groups.yaml' in the base
        Pheno DB directory.
        """
        if not path.is_file() or path.suffix not in (".yaml", ".conf") \
                or path.stem != "groups":
            raise ValueError("Invalid groups config file.")
        config = GPFConfigParser.load_config(str(path), groups_file_schema)
        print(config.groups)
        return [
            PhenotypeGroup(
                group.pheno_id, [
                    registry.get_phenotype_data(child)
                    for child in group.children
                ],
            ) for group in config.groups
        ]


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
