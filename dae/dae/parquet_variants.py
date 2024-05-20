from collections.abc import Iterator, Sequence
from typing import Any, ClassVar, Optional, cast

from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.inmemory_storage.raw_variants import (
    RawFamilyVariants,
    RawVariantsQueryRunner,
    RealAttrFilterType,
)
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from dae.variants_loaders.parquet.loader import ParquetLoader


class ParquetLoaderVariants(RawFamilyVariants):
    """Variants class that utilizes ParquetLoader to fetch variants."""

    def __init__(
        self, data_dir: str, ped_params: Optional[dict] = None,
    ) -> None:
        self.loader = ParquetLoader(data_dir, ped_params)
        super().__init__(self.loader.families)

    def full_variants_iterator(
        self, **kwargs: Any,
    ) -> Iterator[tuple[SummaryVariant, list[FamilyVariant]]]:
        if (regions := kwargs.get("regions")) is None:
            yield from self.loader.fetch_variants()
        else:
            for region in regions:
                yield from self.loader.fetch_variants(repr(region))

    def build_summary_variants_query_runner(
        self, **kwargs: Any,
    ) -> RawVariantsQueryRunner:
        """Return a query runner for the summary variants."""
        filter_func = RawFamilyVariants\
            .summary_variant_filter_function(**kwargs)
        regions = kwargs.get("regions")
        return RawVariantsQueryRunner(
            variants_iterator=self.summary_variants_iterator(regions=regions),
            deserializer=filter_func)

    def build_family_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[Sequence[str]] = None,
        person_ids: Optional[Sequence[str]] = None,
        inheritance: Optional[Sequence[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        **_kwargs: Any,
    ) -> RawVariantsQueryRunner:
        # pylint: disable=too-many-arguments,unused-argument
        """Return a query runner for the family variants."""
        filter_func = RawFamilyVariants.family_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown)

        return RawVariantsQueryRunner(
            variants_iterator=self.family_variants_iterator(regions=regions),
            deserializer=filter_func)


class ParquetGenotypeStorage(GenotypeStorage):
    """Genotype storage for raw parquet files."""

    VALIDATION_SCHEMA: ClassVar[dict] = {
        "storage_type": {"type": "string", "allowed": ["parquet"]},
        "id": {
            "type": "string",
        },
        "read_only": {
            "type": "boolean",
            "default": False,
        },
        "dir": {
            "type": "string",
            "check_with": validate_path,
            "required": True,
        },
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.data_dir = self.storage_config["dir"]

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"parquet"}

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            raise ValueError(
                f"wrong config format for parquet storage: "
                f"{validator.errors}")
        return cast(dict, validator.document)

    def start(self) -> GenotypeStorage:
        return self

    def shutdown(self) -> GenotypeStorage:
        """No resources to close."""
        return self

    def build_backend(
        self, study_config: dict[str, Any],
        _genome: ReferenceGenome,
        _gene_models: Optional[GeneModels],
    ) -> ParquetLoaderVariants:
        pedigree_conf = study_config["genotype_storage"]["files"]["pedigree"]
        return ParquetLoaderVariants(self.data_dir, pedigree_conf["params"])
