from __future__ import annotations

import abc
import functools
import logging
from collections.abc import Iterable
from typing import Any, cast

from dae.effect_annotation.effect import expand_effect_types
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.query_variants.base_query_variants import QueryVariantsBase
from dae.query_variants.query_runners import QueryRunner
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
        self._loaded_variants: dict[str, QueryVariantsBase] = {}

    @property
    def study_configs(self) -> dict[str, dict[str, Any]]:
        return self._study_configs

    @property
    def loaded_variants(self) -> dict[str, QueryVariantsBase]:
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
    ) -> QueryVariantsBase:
        """Construct a query backend for this genotype storage."""

    def build_backend(
        self,
        study_config: dict,
        genome: ReferenceGenome,
        gene_models: GeneModels,
    ) -> None:
        study_id = study_config["id"]
        if study_id not in self.loaded_variants:
            self.study_configs[study_id] = study_config
            self.loaded_variants[study_id] = self._build_backend_internal(
                study_config, genome, gene_models)

    def create_runner(
        self,
        study_id: str,
        kwargs: dict[str, Any],
    ) -> QueryRunner | None:
        study_filters = kwargs.get("study_filters", [])

        regions = kwargs.get("regions")
        genes = kwargs.get("genes")
        effect_types = kwargs.get("effect_types")
        family_ids = kwargs.get("family_ids")
        person_ids = kwargs.get("person_ids")
        inheritance = kwargs.get("inheritance")
        roles = kwargs.get("roles")
        sexes = kwargs.get("sexes")
        affected_statuses = kwargs.get("affected_statuses")
        variant_type = kwargs.get("variant_type")
        real_attr_filter = kwargs.get("real_attr_filter")
        categorical_attr_filter = kwargs.get("categorical_attr_filter")
        ultra_rare = kwargs.get("ultra_rare")
        frequency_filter = kwargs.get("frequency_filter")
        return_reference = kwargs.get("return_reference")
        return_unknown = kwargs.get("return_unknown")
        limit = kwargs.get("limit")
        tags_query = kwargs.get("tags_query")
        if study_filters is not None and study_id not in study_filters:
            return None
        if person_ids is not None and not person_ids:
            return None

        if isinstance(inheritance, str):
            inheritance = [inheritance]

        if effect_types:
            effect_types = expand_effect_types(effect_types)

        def adapt_study_variants(
            study_name: str,
            study_phenotype: str,
            v: FamilyVariant | None,
        ) -> FamilyVariant | None:
            if v is None:
                return None
            for allele in v.alleles:
                if allele.get_attribute("study_name") is None:
                    allele.update_attributes(
                        {"study_name": study_name})
                if allele.get_attribute("study_phenotype") is None:
                    allele.update_attributes(
                        {"study_phenotype": study_phenotype})
            return v

        if study_id not in self.loaded_variants:
            return None

        backend = self.loaded_variants[study_id]
        runner = backend\
            .build_family_variants_query_runner(
                regions=regions,
                genes=genes,
                effect_types=effect_types,
                family_ids=family_ids,
                person_ids=cast(list, person_ids),
                inheritance=inheritance,
                roles=roles,
                sexes=sexes,
                affected_statuses=affected_statuses,
                variant_type=variant_type,
                real_attr_filter=real_attr_filter,
                categorical_attr_filter=categorical_attr_filter,
                ultra_rare=ultra_rare,
                frequency_filter=frequency_filter,
                return_reference=return_reference,
                return_unknown=return_unknown,
                limit=limit,
                tags_query=tags_query,
            )

        if runner is None:
            logger.debug(
                "study %s has no varants... skipping",
                study_id)
            return None

        runner.set_study_id(study_id)
        logger.debug("runner created")

        study_config = self.study_configs[study_id]
        study_name = study_config.get("name", study_id)
        study_phenotype = study_config.get("study_phenotype", "-")

        runner.adapt(functools.partial(
            adapt_study_variants, study_name, study_phenotype))

        return runner

    def create_summary_runner(
        self,
        study_id: str,
        kwargs: dict[str, Any],
    ) -> QueryRunner | None:
        study_filters = kwargs.get("study_filters", [])

        regions = kwargs.pop("regions")
        genes = kwargs.pop("genes")
        effect_types = kwargs.pop("effect_types")
        variant_type = kwargs.pop("variant_type")
        real_attr_filter = kwargs.pop("real_attr_filter")
        category_attr_filter = kwargs.pop("category_attr_filter")
        ultra_rare = kwargs.pop("ultra_rare")
        frequency_filter = kwargs.pop("frequency_filter")
        return_reference = kwargs.pop("return_reference")
        return_unknown = kwargs.pop("return_unknown")
        limit = kwargs.pop("limit")
        if study_filters is not None and study_id not in study_filters:
            return None

        if study_id not in self.loaded_variants:
            return None

        backend = self.loaded_variants[study_id]
        runner = backend.build_summary_variants_query_runner(
                regions=regions,
                genes=genes,
                effect_types=effect_types,
                variant_type=variant_type,
                real_attr_filter=real_attr_filter,
                category_attr_filter=category_attr_filter,
                ultra_rare=ultra_rare,
                frequency_filter=frequency_filter,
                return_reference=return_reference,
                return_unknown=return_unknown,
                limit=limit,
                **kwargs,
            )
        if runner is None:
            return None

        runner.set_study_id(study_id)

        return runner

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
