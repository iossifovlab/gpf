import pathlib
import logging
from typing import Optional, cast
from threading import Lock

from box import Box

from dae.pheno.pheno_data import PhenotypeStudy
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema

logger = logging.getLogger(__name__)


class PhenoRegistry:
    """Class to register phenotype data."""

    CACHE_LOCK = Lock()

    def __init__(self) -> None:
        self._cache: dict[str, PhenotypeStudy] = {}

    def _register_study(self, study: PhenotypeStudy) -> None:
        if study.pheno_id in self._cache:
            raise ValueError(
                f"Pheno ID {study.pheno_id} already loaded."
            )

        self._cache[study.pheno_id] = study

    def register_phenotype_data(
        self, phenotype_data: PhenotypeStudy, lock: bool = True
    ) -> None:
        """Register a phenotype data study."""
        if lock:
            with self.CACHE_LOCK:
                self._register_study(phenotype_data)
        else:
            self._register_study(phenotype_data)

    @classmethod
    def load_pheno_data(cls, path: pathlib.Path) -> PhenotypeStudy:
        """Create a PhenotypeStudy object from a configuration file."""
        if not path.is_file() or (
            not path.name.endswith(".yaml")
            and not path.name.endswith(".conf")
        ):
            raise ValueError("Invalid PhenotypeStudy path")
        config = GPFConfigParser.load_config(str(path), pheno_conf_schema)
        pheno_id = config["phenotype_data"]["name"]
        logger.info("creating phenotype data <%s>", pheno_id)
        phenotype_data = PhenotypeStudy(
            pheno_id,
            dbfile=config["phenotype_data"]["dbfile"],
            browser_dbfile=config["phenotype_data"]["browser_dbfile"],
            config=config["phenotype_data"]
        )
        return phenotype_data

    def has_phenotype_data(self, data_id: str) -> bool:
        with self.CACHE_LOCK:
            return data_id in self._cache

    def get_phenotype_data(self, data_id: str) -> Optional[PhenotypeStudy]:
        with self.CACHE_LOCK:
            return self._cache[data_id]

    def get_phenotype_data_config(self, data_id: str) -> Optional[Box]:
        with self.CACHE_LOCK:
            return cast(Box, self._cache[data_id].config)

    def get_phenotype_data_ids(self) -> list[str]:
        return list(self._cache.keys())
