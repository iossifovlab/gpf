import itertools
import pathlib
from collections.abc import Iterable
from typing import Any, ClassVar, Optional, Union, cast

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
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
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
from dae.variants_loaders.parquet.loader import ParquetLoader


class ParquetLoaderVariants:
    """Variants class that utilizes ParquetLoader to fetch variants."""

    def __init__(self, data_dir: str) -> None:
        self.loader = ParquetLoader(data_dir)

    @property
    def families(self) -> FamiliesData:
        return self.loader.families

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

    @staticmethod
    def build_person_set_collection_query(
        _person_set_collection: PersonSetCollection,
        _person_set_collection_query: tuple[str, set[str]],
    ) -> Optional[Union[tuple, tuple[list[str], list[str]]]]:
        return None


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
        self.data_dir: Optional[str] = self.storage_config.get("dir")

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
        self,
        study_config: dict[str, Any],
        _genome: ReferenceGenome,
        _gene_models: Optional[GeneModels],
    ) -> ParquetLoaderVariants:
        study_id = study_config["id"]
        if self.data_dir is not None:
            study_path = pathlib.Path(self.data_dir, study_id)
            if study_path.exists():
                return ParquetLoaderVariants(str(study_path))
        table_path = study_config["genotype_storage"]["tables"]["summary"]
        return ParquetLoaderVariants(str(pathlib.Path(table_path).parent))

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
    def _do_import_dataset(cls, project: ImportProject) -> Schema2DatasetLayout:
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
                [project], graph.tasks,
            )
            graph.create_task(
                "Creating a study config", DuckDbImportStorage.do_study_config,
                [project, import_task], [import_task],
            )
        return graph
