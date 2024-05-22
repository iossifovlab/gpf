import itertools
from collections.abc import Iterable
from typing import Any, ClassVar, Optional, cast

from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.duckdb_storage.duckdb_import_storage import DuckDbImportStorage
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.import_tools.import_tools import ImportProject
from dae.inmemory_storage.raw_variants import (
    RawFamilyVariants,
    RawVariantsQueryRunner,
    RealAttrFilterType,
)
from dae.schema2_storage.schema2_import_storage import (
    Schema2ImportStorage,
    schema2_project_dataset_layout,
)
from dae.task_graph.graph import TaskGraph
from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


class ParquetLoaderVariants:
    """Variants class that utilizes ParquetLoader to fetch variants."""

    def __init__(
        self, data_dir: str, ped_params: Optional[dict] = None,
    ) -> None:
        self.loader = ParquetLoader(data_dir, ped_params)

    def build_summary_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> RawVariantsQueryRunner:
        """Return a query runner for the summary variants."""

        filter_func = RawFamilyVariants\
            .summary_variant_filter_function(
                regions=regions,
                genes=genes,
                effect_types=effect_types,
                variant_type=variant_type,
                real_attr_filter=real_attr_filter,
                ultra_rare=ultra_rare,
                frequency_filter=frequency_filter,
                return_reference=return_reference,
                return_unknown=return_unknown,
                **kwargs,
            )
        regions = kwargs.get("regions")

        summary_variants_iterator: Iterable
        if regions:
            summary_variants_iterator = itertools.chain(
                self.loader.fetch_summary_variants(region)
                for region in regions
            )
        else:
            summary_variants_iterator = self.loader.fetch_summary_variants()

        if limit is not None:
            summary_variants_iterator = itertools.islice(
                summary_variants_iterator, limit)

        return RawVariantsQueryRunner(
            variants_iterator=summary_variants_iterator,
            deserializer=filter_func)

    def build_family_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        inheritance: Optional[list[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> RawVariantsQueryRunner:
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
            return_unknown=return_unknown,
        )
        regions = kwargs.get("regions")

        family_variants_iterator: Iterable
        if regions:
            family_variants_iterator = itertools.chain(
                self.loader.fetch_family_variants(region)
                for region in regions
            )
        else:
            family_variants_iterator = self.loader.fetch_family_variants()

        if limit is not None:
            family_variants_iterator = itertools.islice(
                family_variants_iterator, limit)

        return RawVariantsQueryRunner(
            variants_iterator=family_variants_iterator,
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
        # FIXME Ask Lubo about these params I used to pass... are they never present in parquet files configs?
        # pedigree_conf = study_config["genotype_storage"]["files"]["pedigree"]
        # return ParquetLoaderVariants(self.data_dir, pedigree_conf["params"])
        return ParquetLoaderVariants(self.data_dir)


class ParquetImportStorage(Schema2ImportStorage):
    """Import storage for Parquet files."""
    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        graph = super().generate_import_task_graph(project)
        # FIXME In duckdb there is first an if check if the instance for this project
        # has a genotype storage, before making the config. should I do this here too?
        layout_task = graph.create_task(
            "Calc layout", schema2_project_dataset_layout,
            [project], graph.tasks,
        )
        graph.create_task(
            "Creating a study config", DuckDbImportStorage.do_study_config,
            [project, layout_task], [layout_task],
        )
        return graph
