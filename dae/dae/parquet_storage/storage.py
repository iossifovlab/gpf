import itertools
import pathlib
from collections.abc import Generator, Iterable
from typing import Any, ClassVar, cast

from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.duckdb_storage.duckdb_import_storage import (
    DuckDbLegacyImportStorage,
)
from dae.genomic_resources.gene_models import (
    GeneModels,
    create_regions_from_genes,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.import_tools.import_tools import ImportProject
from dae.inmemory_storage.raw_variants import (
    RawFamilyVariants,
    RawVariantsQueryRunner,
    RealAttrFilterType,
)
from dae.parquet.schema2.loader import ParquetLoader
from dae.query_variants.base_query_variants import (
    QueryVariants,
    QueryVariantsBase,
)
from dae.schema2_storage.schema2_import_storage import (
    Schema2ImportStorage,
)
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    create_schema2_dataset_layout,
    load_schema2_dataset_layout,
)
from dae.task_graph.graph import TaskGraph
from dae.utils import fs_utils
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant


class ParquetLoaderVariants(QueryVariants):
    """Variants class that utilizes ParquetLoader to fetch variants."""

    def __init__(
        self,
        data_dir: str,
        reference_genome: ReferenceGenome | None = None,
        gene_models: GeneModels | None = None,
    ) -> None:
        self.loader = ParquetLoader.load_from_dir(data_dir)
        super().__init__(self.loader.families)
        self.reference_genome = reference_genome
        self.gene_models = gene_models

    def has_affected_status_queries(self) -> bool:
        return False

    def query_summary_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        """Execute the summary variants query and yields summary variants."""
        raise NotImplementedError

    def query_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles_in_parent: str | None = None,
        roles_in_child: str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        """Execute the family variants query and yields family variants."""
        raise NotImplementedError

    def build_summary_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
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

        if genes is not None:
            assert self.gene_models is not None
            regions = create_regions_from_genes(
                self.gene_models, genes, regions,
            )

        summary_variants_iterator: Iterable
        if regions:
            summary_variants_iterator = itertools.chain.from_iterable(
                self.loader.fetch_summary_variants(region)
                for region in regions
            )
        else:
            summary_variants_iterator = self.loader.fetch_summary_variants()

        return RawVariantsQueryRunner(
            variants_iterator=summary_variants_iterator,
            deserializer=filter_func)

    def build_family_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **_kwargs: Any,
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

        if genes is not None:
            assert self.gene_models is not None
            regions = create_regions_from_genes(
                self.gene_models, genes, regions,
            )

        family_variants_iterator: Iterable
        if regions:
            family_variants_iterator = itertools.chain.from_iterable(
                self.loader.fetch_family_variants(region)
                for region in regions
            )
        else:
            family_variants_iterator = self.loader.fetch_family_variants()

        return RawVariantsQueryRunner(
            variants_iterator=family_variants_iterator,
            deserializer=filter_func)


class ParquetGenotypeStorage(GenotypeStorage):
    """Genotype storage for raw parquet files."""

    VALIDATION_SCHEMA: ClassVar[dict] = {
        "storage_type": {
            "type": "string",
            "allowed": ["parquet"],
        },
        "id": {
            "type": "string",
        },
        "dir": {
            "type": "string",
            "check_with": validate_path,
        },
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.data_dir: str | None = self.storage_config.get("dir")

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"parquet"}

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)  # type: ignore[call-arg]
        if not validator.validate(config):  # type: ignore[no-untyped-call]
            raise ValueError(
                f"wrong config format for parquet storage: "
                f"{validator.errors}")  # type: ignore[no-untyped-call]
        return cast(dict, validator.document)  # type: ignore[no-untyped-call]

    def start(self) -> GenotypeStorage:
        return self

    def shutdown(self) -> GenotypeStorage:
        """No resources to close."""
        return self

    def _build_backend_internal(
        self,
        study_config: dict[str, Any],
        genome: ReferenceGenome,
        gene_models: GeneModels | None,
    ) -> QueryVariantsBase:
        study_id = study_config["id"]
        if self.data_dir is not None:
            study_path = pathlib.Path(self.data_dir, study_id)
            if study_path.exists():
                path = study_path
            else:
                raise FileNotFoundError(
                    f"Study {study_id} not found in {self.data_dir}")
        else:
            table_path = study_config["genotype_storage"]["tables"]["summary"]
            path = pathlib.Path(table_path).parent
        return cast(
            QueryVariantsBase,
            ParquetLoaderVariants(str(path), genome, gene_models),
        )

    def import_dataset(
        self, study_id: str, layout: Schema2DatasetLayout,
    ) -> Schema2DatasetLayout:
        """Copy study parquet dataset into Schema2 genotype storage."""
        if self.data_dir is None:
            raise ValueError("Cannot import with no data dir configured!")
        import_layout = create_schema2_dataset_layout(
            str(pathlib.Path(self.data_dir, study_id)))
        fs_utils.copy(import_layout.study, layout.study)
        return import_layout


class ParquetImportStorage(Schema2ImportStorage):
    """Import storage for Parquet files."""

    @classmethod
    def _do_import_dataset(
        cls, project: ImportProject,
    ) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, ParquetGenotypeStorage)
        layout = load_schema2_dataset_layout(project.get_parquet_dataset_dir())
        if genotype_storage.data_dir is not None:
            layout = genotype_storage.import_dataset(project.study_id, layout)
        return layout

    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        graph = super().generate_import_task_graph(project)
        if project.has_genotype_storage():
            import_task = graph.create_task(
                "Import dataset", self._do_import_dataset,
                args=[project], deps=graph.tasks,
            )
            graph.create_task(
                "Creating a study config",
                DuckDbLegacyImportStorage.do_study_config,
                args=[project, import_task], deps=[import_task],
            )
        return graph
