from __future__ import annotations

import abc
import logging
from typing import Dict, cast, Any

from deprecation import deprecated


logger = logging.getLogger(__file__)


class GenotypeStorage(abc.ABC):
    """Base class for genotype storages."""

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_id = storage_config["id"]
        self.storage_config = storage_config
        self.is_open = False

    # @property  # type: ignore
    # @deprecated(details="switch to using storage_id")
    # def id(self):
    #     return self.storage_id

    @deprecated(details="pending remove from the API")
    def is_impala(self):  # pylint: disable=no-self-use
        return False

    @deprecated(details="pending remove from the API")
    def is_filestorage(self):  # pylint: disable=no-self-use
        return False

    def get_storage_type(self) -> str:
        return cast(str, self.storage_config["storage_type"])

    @abc.abstractmethod
    def open(self) -> GenotypeStorage:
        """Allocate all resources needed for the genotype storage to work."""

    @abc.abstractmethod
    def build_backend(self, study_config, genome, gene_models):
        """Construct a query backend for this genotype storage."""

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
