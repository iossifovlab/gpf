"""Defines GPFInstance class that gives access to different parts of GPF."""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

import logging
import os
from functools import cached_property
from pathlib import Path
from typing import Any, cast

import yaml
from box import Box

from dae.annotation.annotation_factory import (
    RawPipelineConfig,
    build_annotation_pipeline,
)
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.common_reports.common_report import CommonReport
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.gene_profile import gene_profiles_config
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.gene_profile.db import GeneProfileDB
from dae.gene_profile.statistic import GPStatistic
from dae.gene_scores.gene_scores import GeneScore
from dae.gene_scores.gene_scores import ScoreDesc as GeneScoreDesc
from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.gene_sets.gene_sets_db import (
    GeneSetsDb,
    build_gene_set_collection_from_resource,
)
from dae.genomic_resources.gene_models import GeneModels, TranscriptModel
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_scores.scores import GenomicScoresRegistry
from dae.pheno.pheno_data import (
    PhenotypeData,
    get_pheno_db_dir,
)
from dae.pheno.registry import PhenoRegistry
from dae.pheno.storage import (
    PhenotypeStorage,
    PhenotypeStorageRegistry,
)
from dae.studies.study import GenotypeData
from dae.studies.variants_db import VariantsDb
from dae.utils.fs_utils import find_directory_with_a_file

logger = logging.getLogger(__name__)


class GPFInstance:
    """Class to access different parts of a GPF instance."""

    # pylint: disable=too-many-public-methods
    @staticmethod
    def _build_gpf_config(
        config_filename: str | Path | None = None,
    ) -> tuple[Box, Path, Path]:
        dae_dir: Path | None
        if config_filename is not None:
            config_filename = Path(config_filename)
            dae_dir = config_filename.parent
        else:
            if os.environ.get("DAE_DB_DIR"):
                dae_dir = Path(os.environ["DAE_DB_DIR"])
                config_filename = Path(dae_dir) / "gpf_instance.yaml"
            else:
                dae_dir = find_directory_with_a_file("gpf_instance.yaml")
                if dae_dir is None:
                    raise ValueError("unable to locate GPF instance directory")
                config_filename = dae_dir / "gpf_instance.yaml"
        assert config_filename is not None
        if not config_filename.exists():
            raise ValueError(
                f"GPF instance config <{config_filename}> does not exists")
        dae_config = GPFConfigParser.load_config(
            str(config_filename), dae_conf_schema)
        return dae_config, dae_dir, config_filename

    @staticmethod
    def build(
            config_filename: str | Path | None = None,
            **kwargs: Any) -> GPFInstance:
        """Construct and return a GPF instance.

        If the config_filename is None, tries to discover the GPF instance.
        First check if a DAE_DB_DIR environment variable is defined and if
        defined use it as a GPF instance directory.

        Otherwise look for a gpf_instance.yaml file in the current directory
        and its parents. If found use it as a configuration file.
        """
        dae_config, dae_dir, dae_config_path = \
            GPFInstance._build_gpf_config(config_filename)
        return GPFInstance(
            dae_config, dae_dir, dae_config_path, **kwargs,
        )

    def __init__(
            self,
            dae_config: Box,
            dae_dir: str | Path,
            dae_config_path: Path,
            **kwargs: dict[str, Any]):
        assert dae_dir is not None

        self.dae_config = dae_config
        self.dae_dir = str(dae_dir)
        self.dae_config_path = dae_config_path

        self.instance_id = self.dae_config.get("instance_id")

        assert self.instance_id is not None, "No instance ID provided."

        self._grr = cast(GenomicResourceRepo, kwargs.get("grr"))
        self._reference_genome = cast(
            ReferenceGenome, kwargs.get("reference_genome"),
        )
        self._gene_models = cast(
            GeneModels,
            kwargs.get("gene_models"),
        )
        self._annotation_pipeline: AnnotationPipeline | None = None

        cache_dir = self.dae_config.get("cache_path")
        if cache_dir:
            self.cache_dir: Path | None = Path(self.dae_dir, cache_dir)
        else:
            self.cache_dir = None

    def get_cache_path(self, prefix: str) -> Path | None:
        if self.cache_dir is not None:
            return self.cache_dir / prefix
        return None

    def load(self) -> GPFInstance:
        """Load all GPF instance attributes."""
        # pylint: disable=pointless-statement
        self.reference_genome  # noqa: B018
        self.gene_models  # noqa: B018
        self.gene_sets_db  # noqa: B018
        self._pheno_registry  # noqa: B018
        self._variants_db  # noqa: B018
        self.denovo_gene_sets_db  # noqa: B018
        self.genomic_scores  # noqa: B018
        self.genotype_storages  # noqa: B018
        return self

    @cached_property
    def grr(self) -> GenomicResourceRepo:
        """Return genomic resource repository configured for GPF instance."""
        if self._grr is not None:
            return self._grr

        # pylint: disable=import-outside-toplevel
        from dae.genomic_resources import build_genomic_resource_repository
        if self.dae_config.grr:
            self._grr = build_genomic_resource_repository(
                self.dae_config.grr.to_dict())
            return self._grr
        self._grr = build_genomic_resource_repository()
        return self._grr

    @cached_property
    def reference_genome(self) -> ReferenceGenome:
        """Return reference genome defined in the GPFInstance config."""
        if self._reference_genome is not None:
            return self._reference_genome

        # pylint: disable=import-outside-toplevel
        from dae.genomic_resources.reference_genome import (
            build_reference_genome_from_resource,
        )

        resource = self.grr.get_resource(
            self.dae_config.reference_genome.resource_id)
        result = build_reference_genome_from_resource(resource)
        result.open()
        return result

    @cached_property
    def gene_models(self) -> GeneModels:
        """Return gene models used in the GPF instance."""
        if self._gene_models is not None:
            return self._gene_models

        # pylint: disable=import-outside-toplevel
        from dae.genomic_resources.gene_models import (
            build_gene_models_from_resource,
        )

        resource = self.grr.get_resource(
            self.dae_config.gene_models.resource_id)
        assert resource is not None, \
            self.dae_config.gene_models.resource_id
        result = build_gene_models_from_resource(resource)
        result.load()
        return result

    def get_transcript_models(
        self, gene_symbol: str,
    ) -> tuple[str | None, list[TranscriptModel] | None]:
        """Get gene model by gene symbol."""
        gene_symbol = gene_symbol.lower()
        gene_models = self.gene_models.gene_models

        for k, v in gene_models.items():
            if gene_symbol == k.lower():
                return k, v

        return None, None

    def _get_default_phenotype_storage_config(self) -> dict:
        base_dir = get_pheno_db_dir(self.dae_config)
        return {
            "default": "default_pheno_storage",
            "storages": [
                {
                    "id": "default_pheno_storage",
                    "base_dir": base_dir,
                },
            ],
        }

    @cached_property
    def phenotype_storages(self) -> PhenotypeStorageRegistry:
        """
        Get phenotype storage registry.

        Will load if not cached.
        """
        registry = PhenotypeStorageRegistry()

        if "phenotype_storage" in self.dae_config:
            storages_config = self.dae_config["phenotype_storage"]
        else:
            storages_config = self._get_default_phenotype_storage_config()

        default_id = storages_config["default"]
        for storage_config in storages_config["storages"]:
            storage_config["base_dir"] = str(Path(
                self.dae_dir, storage_config["base_dir"],
            ))
            storage = PhenotypeStorage.from_config(storage_config)
            if storage.storage_id == default_id:
                registry.register_default_storage(storage)
            else:
                registry.register_phenotype_storage(storage)

        return registry

    def get_pheno_cache_path(self) -> Path:
        pheno_cache_dir = self.get_cache_path("pheno")
        if pheno_cache_dir is None:
            pheno_data_dir = get_pheno_db_dir(self.dae_config)
            return Path(pheno_data_dir)
        return pheno_cache_dir

    @cached_property
    def _pheno_registry(self) -> PhenoRegistry:
        pheno_data_dir = get_pheno_db_dir(self.dae_config)
        config_files = GPFConfigParser.collect_directory_configs(
            pheno_data_dir,
        )
        logger.info("phenotype data config files: %s", config_files)
        configurations = [
            GPFConfigParser.load_config_dict(file, pheno_conf_schema)
            for file in config_files
        ]
        logger.debug("phenotype data configurations: %s", configurations)
        return PhenoRegistry(
            self.phenotype_storages,
            configurations=configurations,
            browser_cache_path=self.get_pheno_cache_path(),
        )

    @cached_property
    def gene_scores_db(self) -> Any:
        """Load and return gene scores db."""
        from dae.gene_scores.gene_scores import (
            GeneScoresDb,
            build_gene_score_from_resource,
        )
        if self.dae_config.gene_scores_db is None:
            return GeneScoresDb([])

        gene_scores = self.dae_config.gene_scores_db.gene_scores
        collections = []
        for score in gene_scores:
            resource = self.grr.get_resource(score)
            if resource is None:
                logger.error("unable to find gene score: %s", score)
                continue
            collections.append(build_gene_score_from_resource(resource))

        return GeneScoresDb(collections)

    @cached_property
    def genomic_scores(self) -> GenomicScoresRegistry:
        """Load and return genomic scores db."""
        pipeline = self.get_annotation_pipeline()
        return GenomicScoresRegistry.build_genomic_scores_registry(pipeline)

    @cached_property
    def genotype_storages(self) -> Any:
        """Construct and return genotype storage registry."""
        # pylint: disable=import-outside-toplevel
        from dae.genotype_storage.genotype_storage_registry import (
            GenotypeStorageRegistry,
        )
        registry = GenotypeStorageRegistry()
        internal_storage = registry.register_storage_config({
            "id": "internal",
            "storage_type": "duckdb_parquet",
            "base_dir": os.path.join(self.dae_dir, "internal_storage"),
        })

        registry.register_default_storage(internal_storage)

        if self.dae_config.genotype_storage:
            registry.register_storages_configs(
                self.dae_config.genotype_storage)
        return registry

    @cached_property
    def _variants_db(self) -> VariantsDb:
        return VariantsDb(
            self.dae_config,
            self.reference_genome,
            self.gene_models,
            self.get_annotation_pipeline().get_attributes(),
            self.genotype_storages,
        )

    @cached_property
    def _gene_profile_db(self) -> GeneProfileDB:
        config = None if self._gene_profile_config is None else\
            self._gene_profile_config.to_dict()

        # In case of sqlite db still used
        if os.path.isfile(os.path.join(self.dae_dir, "gpdb.duckdb")):
            db_name = "gpdb.duckdb"
        else:
            logger.info("Using legacy sqlite gpdb!")
            db_name = "gpdb"
        return GeneProfileDB(
            config,
            os.path.join(self.dae_dir, db_name),
        )

    def reload(self) -> None:
        """Reload GPF instance studies, de Novo gene sets, etc."""
        self._variants_db.reload()
        self.denovo_gene_sets_db.reload()

    @cached_property
    def _gene_profile_config(self) -> Box | None:
        gp_config = self.dae_config.gene_profiles_config
        config_filename = None

        if gp_config is None:
            config_filename = os.path.join(
                self.dae_dir, "geneProfiles.yaml")
            if not os.path.exists(config_filename):
                return None
        else:
            if not os.path.exists(gp_config.conf_file):
                return None
            config_filename = gp_config.conf_file

        assert config_filename is not None
        return GPFConfigParser.load_config(
            config_filename,
            gene_profiles_config,
        )

    @cached_property
    def gene_sets_db(self) -> GeneSetsDb:
        """Return GeneSetsDb populated with gene sets from the GPFInstance."""
        logger.debug("creating new instance of GeneSetsDb")
        if "gene_sets_db" in self.dae_config:
            gsc_ids = self.dae_config.gene_sets_db.gene_set_collections
            gscs = []
            for gsc_id in gsc_ids:
                resource = self.grr.get_resource(gsc_id)
                if resource is None:
                    logger.error("can't find resource %s", gsc_id)
                    continue
                gscs.append(
                    build_gene_set_collection_from_resource(resource),
                )

            return GeneSetsDb(gscs)

        logger.debug("No gene sets DB configured")
        return GeneSetsDb([])

    @cached_property
    def denovo_gene_sets_db(self) -> DenovoGeneSetsDb:
        return DenovoGeneSetsDb(self)

    def get_genotype_data_ids(self) -> list[str]:
        # pylint: disable=unused-argument
        return cast(list[str], (
            self._variants_db.get_all_genotype_study_ids()
            + self._variants_db.get_all_genotype_group_ids()
        ))

    def get_genotype_data(self, genotype_data_id: str) -> GenotypeData:
        genotype_data_study = self._variants_db.get_genotype_study(
            genotype_data_id)
        if genotype_data_study:
            return genotype_data_study
        return cast(
            GenotypeData,
            self._variants_db.get_genotype_group(genotype_data_id),
        )

    def get_all_genotype_data(self) -> list[GenotypeData]:
        genotype_studies = self._variants_db.get_all_genotype_studies()
        genotype_data_groups = self._variants_db.get_all_genotype_groups()
        return cast(
            list[GenotypeData], genotype_studies + genotype_data_groups,
        )

    def get_genotype_data_config(self, genotype_data_id: str) -> Box | None:
        config = self._variants_db.get_genotype_study_config(genotype_data_id)
        if config is not None:
            return config
        return cast(Box, self._variants_db.get_genotype_group_config(
            genotype_data_id,
        ))

    # Phenotype data
    def get_phenotype_data_ids(self) -> list[str]:
        return self._pheno_registry.get_phenotype_data_ids()

    def has_phenotype_data(
        self, phenotype_data_id: str,
    ) -> bool:
        return self._pheno_registry.has_phenotype_data(phenotype_data_id)

    def get_phenotype_data(
        self, phenotype_data_id: str,
    ) -> PhenotypeData:
        return self._pheno_registry.get_phenotype_data(phenotype_data_id)

    def get_all_phenotype_data(self) -> list[PhenotypeData]:
        return self._pheno_registry.get_all_phenotype_data()

    def get_phenotype_data_config(
        self, phenotype_data_id: str,
    ) -> dict | None:
        return self._pheno_registry.get_phenotype_data_config(
            phenotype_data_id)

    # Gene scores
    def has_gene_score(self, gene_score_id: str) -> bool:
        return gene_score_id in self.gene_scores_db

    def get_gene_score(self, gene_score_id: str) -> GeneScore:
        return cast(
            GeneScore, self.gene_scores_db.get_gene_score(gene_score_id),
        )

    def get_gene_score_desc(self, score_id: str) -> GeneScoreDesc:
        return cast(
            GeneScoreDesc, self.gene_scores_db.get_score_desc(score_id),
        )

    def get_all_gene_scores(self) -> list[GeneScore]:
        return cast(list[GeneScore], self.gene_scores_db.get_gene_scores())

    def get_all_gene_score_descs(self) -> list[GeneScoreDesc]:
        return cast(list[GeneScoreDesc], self.gene_scores_db.get_scores())

    # Common reports
    def get_common_report(self, study_id: str) -> CommonReport | None:
        """Load and return common report (dataset statistics) for a study."""
        study = self.get_genotype_data(study_id)
        if study is None:
            if self.has_phenotype_data(study_id):
                study = self.get_phenotype_data(study_id)
            else:
                return None
        return study.get_common_report()

    def get_all_common_report_configs(self) -> list[Box]:
        """Return all common report configuration."""
        configs = []
        local_ids = self.get_genotype_data_ids()
        for gd_id in local_ids:
            config = self.get_genotype_data_config(gd_id)
            if config is not None and config.common_report is not None:
                configs.append(config.common_report)
        return configs

    # Variants DB
    def get_dataset(self, dataset_id: str) -> GenotypeData:
        return cast(GenotypeData, self._variants_db.get(dataset_id))

    # GP
    def get_gp_configuration(self) -> Box:
        return cast(Box, self._gene_profile_db.configuration)

    def get_gp_statistic(self, gene_symbol: str) -> GPStatistic:
        return cast(
            GPStatistic, self._gene_profile_db.get_gp(gene_symbol),
        )

    def query_gp_statistics(
        self,
        page: int,
        symbol_like: str | None = None,
        sort_by: str | None = None,
        order: str | None = None,
    ) -> list[GPStatistic]:
        """Query AGR statistics and return results."""
        rows = self._gene_profile_db.query_gps(
            page, symbol_like, sort_by, order,
        )
        statistics = list(map(
            self._gene_profile_db.gp_from_table_row,
            rows,
        ))
        return cast(list[GPStatistic], statistics)

    def list_gp_gene_symbols(
        self,
        page: int,
        symbol_like: str | None = None,
    ) -> list[str]:
        """Query AGR statistics and return results."""
        return self._gene_profile_db.list_symbols(
            page, symbol_like,
        )

    def _construct_import_effect_annotator_config(
        self,
    ) -> dict[str, Any]:
        """Construct import effect annotator."""
        genome = self.reference_genome
        gene_models = self.gene_models

        return {
            "effect_annotator": {
                "genome": genome.resource_id,
                "gene_models": gene_models.resource_id,
                "attributes": [
                    {
                        "source": "allele_effects",
                        "name": "allele_effects",
                        "internal": True,
                    },
                    "worst_effect",
                    "gene_effects",
                    "effect_details",
                    {
                        "source": "gene_list",
                        "name": "gene_list",
                        "internal": True,
                    },
                ],
            },
        }

    def get_annotation_pipeline_config(
        self,
    ) -> RawPipelineConfig:
        """Return the annotation pipeline config."""
        pipeline_config = []
        if self.dae_config.annotation is not None:
            if "config" in self.dae_config.annotation and \
                    "conf_file" in self.dae_config.annotation:
                logger.warning(
                    "Two annotation config files provided, "
                    "both inline and in file.",
                )

            if "config" in self.dae_config.annotation:
                pipeline_config = [dict(annotator) for annotator in
                                   self.dae_config.annotation.config]
            elif "conf_file" in self.dae_config.annotation and \
                    isinstance(self.dae_config.annotation.conf_file, str):
                config_filename = self.dae_config.annotation.conf_file
                if not os.path.abspath(config_filename):
                    config_filename = os.path.join(
                        self.dae_dir, config_filename,
                    )
                if not os.path.exists(config_filename):
                    raise ValueError(
                        f"annotation config file not found: {config_filename}")

                with open(config_filename, "rt", encoding="utf8") as infile:
                    pipeline_config = yaml.safe_load(infile.read())
            else:
                logger.warning(
                    "Path to annotation configuration or "
                    "inlined configuration not provided!",
                )
        if isinstance(pipeline_config, dict):
            annotators = pipeline_config.get("annotators", [])
            annotators.insert(
                0, self._construct_import_effect_annotator_config())
        elif isinstance(pipeline_config, list):
            pipeline_config.insert(
                0, self._construct_import_effect_annotator_config())
        else:
            raise TypeError(
                f"unexpected annotation pipeline config: "
                f"{pipeline_config}")
        return cast(RawPipelineConfig, pipeline_config)

    def get_annotation_pipeline(self) -> AnnotationPipeline:
        """Return the annotation pipeline configured in the GPF instance."""
        if self._annotation_pipeline is None:
            pipeline_config = self.get_annotation_pipeline_config()
            pipeline = build_annotation_pipeline(pipeline_config, self.grr)

            self._annotation_pipeline = pipeline

        return self._annotation_pipeline
