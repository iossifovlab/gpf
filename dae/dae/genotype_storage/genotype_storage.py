from __future__ import annotations

import abc
import logging
from typing import Dict, Any

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels


logger = logging.getLogger(__file__)


class GenotypeStorage(abc.ABC):
    """Base class for genotype storages."""

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_config = \
            self.validate_and_normalize_config(storage_config)
        self.storage_id = self.storage_config["id"]

    @classmethod
    def validate_and_normalize_config(cls, config: Dict) -> Dict:
        """Normalize and validate the genotype storage configuration.

        When validation passes returns the normalized and validated
        annotator configuration dict.

        When validation fails, raises ValueError.

        All genotype storage configurations are required to have:

        * "storage_type" - which storage type this configuration is used for;

        * "id" - the ID of the genotype storage instance that will be created.

        """
        if config.get("id") is None:
            raise ValueError(
                f"genotype storage without ID; 'id' is required: {config}")
        if config.get("storage_type") is None:
            raise ValueError(
                f"genotype storage without type; 'storage_type' is required: "
                f"{config}")
        if config["storage_type"] != cls.get_storage_type():
            raise ValueError(
                f"storage configuration for <{config['storage_type']}> passed "
                f"to genotype storage class type <{cls.get_storage_type()}>")
        return config

    @classmethod
    @abc.abstractmethod
    def get_storage_type(cls) -> str:
        """Return the genotype storage type."""

    @abc.abstractmethod
    def start(self) -> GenotypeStorage:
        """Allocate all resources needed for the genotype storage to work."""

    @abc.abstractmethod
    def shutdown(self) -> GenotypeStorage:
        """Frees all resources used by the genotype storage to work."""

    @abc.abstractmethod
    def build_backend(
            self,
            study_config: dict,
            genome: ReferenceGenome,
            gene_models: GeneModels) -> Any:
        """Construct a query backend for this genotype storage."""
