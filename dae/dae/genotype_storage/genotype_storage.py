from __future__ import annotations

import abc
import logging
from collections.abc import Iterable
from typing import Any, cast

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.query_variants.base_query_variants import QueryVariants
from dae.variants.family_variant import FamilyVariant

logger = logging.getLogger(__name__)


class GenotypeStorage(abc.ABC):
    """Base class for genotype storages."""

    def __init__(
        self, storage_config: dict[str, Any],
    ):
        self.storage_config = \
            self.validate_and_normalize_config(storage_config)
        self.storage_id = self.storage_config["id"]
        self.storage_type = cast(str, self.storage_config["storage_type"])
        self._read_only = cast(
            bool, self.storage_config.get("read_only", False))
        self._study_configs: dict[str, dict[str, Any]] = {}
        self._loaded_variants: dict[str, QueryVariants] = {}

    @property
    def study_configs(self) -> dict[str, dict[str, Any]]:
        return self._study_configs

    @property
    def loaded_variants(self) -> dict[str, QueryVariants]:
        return self._loaded_variants

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
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
        if config["storage_type"] not in cls.get_storage_types():
            raise ValueError(
                f"storage configuration for <{config['storage_type']}> passed "
                f"to genotype storage class type <{cls.get_storage_types()}>")
        return config

    def is_read_only(self) -> bool:
        return self._read_only

    @property
    def read_only(self) -> bool:
        return self._read_only

    @classmethod
    @abc.abstractmethod
    def get_storage_types(cls) -> set[str]:
        """Return the genotype storage type."""

    @abc.abstractmethod
    def start(self) -> GenotypeStorage:
        """Allocate all resources needed for the genotype storage to work."""

    @abc.abstractmethod
    def shutdown(self) -> GenotypeStorage:
        """Frees all resources used by the genotype storage to work."""

    @abc.abstractmethod
    def _build_backend_internal(
        self,
        study_config: dict,
        genome: ReferenceGenome,
        gene_models: GeneModels,
    ) -> QueryVariants:
        """Construct a query backend for this genotype storage."""

    def build_backend(
        self,
        study_config: dict,
        genome: ReferenceGenome,
        gene_models: GeneModels,
    ) -> None:
        study_id = study_config["id"]
        if study_id not in self.loaded_variants:
            self.loaded_variants[study_id] = self._build_backend_internal(
                study_config, genome, gene_models)

    def query_variants(
        self,
        study_id: str,
        kwargs: dict[str, Any],
    ) -> Iterable[FamilyVariant] | None:
        """Return an iterable for variants."""
        if study_id not in self.study_configs:
            return None
        if study_id not in self.loaded_variants:
            raise ValueError(
                f"{study_id} has no loaded QueryVariants backend!")

        return self.loaded_variants[study_id].query_variants(**kwargs)
