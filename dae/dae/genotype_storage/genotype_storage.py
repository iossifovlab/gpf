from __future__ import annotations

import abc
import logging
import weakref
from typing import Dict, cast, Any, ClassVar

from deprecation import deprecated


logger = logging.getLogger(__file__)


class GenotypeStorage(abc.ABC):
    """Base class for genotype storages."""

    _instances: ClassVar[weakref.WeakSet[GenotypeStorage]] = weakref.WeakSet()

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_config = self.validate_config(storage_config)
        self.storage_id = self.storage_config["id"]
        self._instances.add(self)

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        """Normalize and validate the genotype storage configuration.

        When validation passes returns the normalized and validated
        annotator configuration dict.

        When validation fails, raises ValueError.
        """
        if config.get("id") is None:
            raise ValueError(
                "genotype storage without ID; 'id' is required")
        if config.get("storage_type") is None:
            raise ValueError(
                "genotype storage without type; 'storage_type' is required")
        return config

    @deprecated(details="pending remove from the API")
    def is_impala(self):  # pylint: disable=no-self-use
        return False

    @deprecated(details="pending remove from the API")
    def is_filestorage(self):  # pylint: disable=no-self-use
        return False

    def get_storage_type(self) -> str:
        return cast(str, self.storage_config["storage_type"])

    @abc.abstractmethod
    def start(self) -> GenotypeStorage:
        """Allocate all resources needed for the genotype storage to work."""

    @abc.abstractmethod
    def shutdown(self) -> GenotypeStorage:
        """Frees all resources used by the genotype storage to work."""

    @abc.abstractmethod
    def build_backend(self, study_config, genome, gene_models):
        """Construct a query backend for this genotype storage."""

    @deprecated(details="pending remove from the API")
    @abc.abstractmethod
    def simple_study_import(
            self,
            study_id,
            families_loader=None,
            variant_loaders=None,
            study_config=None,
            **kwargs):
        """Handle import of simple studies."""
        raise NotImplementedError()


# @atexit.register
# def shutdown_genotype_storages():
#     """Shutdown all genotype storages created."""
#     # pylint: disable=protected-access
#     for storage in list(GenotypeStorage._instances):
#         logger.info("closing genotype storage %s", storage.storage_id)
#         try:
#             storage.close()
#         except Exception:  # pylint: disable=broad-except
#             pass
