"""Defines GPFInstance class that gives access to different parts of GPF."""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

import os
import logging
from functools import cached_property
from typing import Optional, Union, Any, cast
from pathlib import Path

import yaml
from box import Box

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.gene_profile.statistic import GPStatistic
from dae.gene.gene_scores import GeneScore
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome

from dae.genomic_resources.repository import GenomicResourceRepo
from dae.utils.fs_utils import find_directory_with_a_file
from dae.studies.study import GenotypeData
from dae.gene.scores import GenomicScoresRegistry
from dae.gene.gene_scores import ScoreDesc as GeneScoreDesc
from dae.gene.gene_sets_db import GeneSet, GeneSetsDb, \
    build_gene_set_collection_from_resource
from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.common_reports.common_report import CommonReport

from dae.studies.variants_db import VariantsDb

from dae.pheno.registry import PhenoRegistry
from dae.pheno.pheno_data import PhenotypeData, get_pheno_db_dir

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.gene_profile import gene_profiles_config

from dae.gene_profile.db import GeneProfileDB
from dae.annotation.annotation_factory import build_annotation_pipeline


logger = logging.getLogger(__name__)


class GPFInstance:
    """Class to access different parts of a GPF instance."""

    # pylint: disable=too-many-public-methods
    @staticmethod
    def _build_gpf_config(
        config_filename: Optional[Union[str, Path]] = None
    ) -> tuple[Box, Path]:
        dae_dir: Optional[Path]
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
        return dae_config, dae_dir

    @staticmethod
    def build(
            config_filename: Optional[Union[str, Path]] = None,
            **kwargs: Any) -> GPFInstance:
        """Construct and return a GPF instance.

        If the config_filename is None, tries to discover the GPF instance.
        First check if a DAE_DB_DIR environment variable is defined and if
        defined use it as a GPF instance directory.

        Otherwise look for a gpf_instance.yaml file in the current directory
        and its parents. If found use it as a configuration file.
        """
        dae_config, dae_dir = GPFInstance._build_gpf_config(config_filename)
        return GPFInstance(dae_config, dae_dir, **kwargs)

    def __init__(
            self,
            dae_config: Box,
            dae_dir: Union[str, Path],
            **kwargs: dict[str, Any]):
        assert dae_dir is not None

        self.dae_config = dae_config
        self.dae_dir = str(dae_dir)

        self.instance_id = self.dae_config.get("instance_id")

        assert self.instance_id is not None, "No instance ID provided."

        self._grr = cast(GenomicResourceRepo, kwargs.get("grr"))
        self._reference_genome = cast(
            ReferenceGenome, kwargs.get("reference_genome")
        )
        self._gene_models = cast(
            GeneModels,
            kwargs.get("gene_models")
        )
        self._annotation_pipeline: Optional[AnnotationPipeline] = None

    def load(self) -> GPFInstance:
        """Load all GPF instance attributes."""
        # pylint: disable=pointless-statement
        self.reference_genome
        self.gene_models
        self.gene_sets_db
        self._pheno_registry
        self._variants_db
        self.denovo_gene_sets_db
        self.genomic_scores
        self.genotype_storages
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
        from dae.genomic_resources.reference_genome import \
            build_reference_genome_from_resource

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
        from dae.genomic_resources.gene_models import \
            build_gene_models_from_resource

        resource = self.grr.get_resource(
            self.dae_config.gene_models.resource_id)
        assert resource is not None, \
            self.dae_config.gene_models.resource_id
        result = build_gene_models_from_resource(resource)
        result.load()
        return result

    @cached_property
    def _pheno_registry(self) -> PhenoRegistry:
        pheno_data_dir = get_pheno_db_dir(self.dae_config)
        registry = PhenoRegistry()
        logger.error("pheno registry created: %s", id(registry))
        pheno_configs = GPFConfigParser.collect_directory_configs(
            pheno_data_dir
        )

        with PhenoRegistry.CACHE_LOCK:
            for config in pheno_configs:
                logger.info("loading phenotype data from config: %s", config)
                registry.register_phenotype_data(
                    PhenoRegistry.load_pheno_data(Path(config)),
                    lock=False
                )
        return registry

    @cached_property
    def gene_scores_db(self) -> Any:
        """Load and return gene scores db."""
        from dae.gene.gene_scores import GeneScoresDb, \
            build_gene_score_from_resource
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
        from dae.genotype_storage.genotype_storage_registry import \
            GenotypeStorageRegistry
        registry = GenotypeStorageRegistry()
        internal_storage = registry.register_storage_config({
            "id": "internal",
            "storage_type": "inmemory",
            "dir": os.path.join(self.dae_dir, "internal_storage"),
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
            self.genotype_storages,
        )

    @cached_property
    def _gene_profile_db(self) -> GeneProfileDB:
        config = None if self._gene_profile_config is None else\
            self._gene_profile_config.to_dict()

        gpdb = GeneProfileDB(
            config,
            os.path.join(self.dae_dir, "gpdb")
        )
        return gpdb

    def reload(self) -> None:
        """Reload GPF instance studies, de Novo gene sets, etc."""
        self._variants_db.reload()
        self.denovo_gene_sets_db.reload()

    @cached_property
    def _gene_profile_config(self) -> Optional[Box]:
        gp_config = self.dae_config.gene_profiles_config
        config_filename = None

        if gp_config is None:
            config_filename = os.path.join(
                self.dae_dir, "geneProfiles.conf")
            if not os.path.exists(config_filename):
                return None
        else:
            if not os.path.exists(gp_config.conf_file):
                return None
            config_filename = gp_config.conf_file

        assert config_filename is not None
        return GPFConfigParser.load_config(
            config_filename,
            gene_profiles_config
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
                    build_gene_set_collection_from_resource(resource)
                )

            return GeneSetsDb(gscs)

        logger.debug("No gene sets DB configured")
        return GeneSetsDb([])

    @cached_property
    def denovo_gene_sets_db(self) -> DenovoGeneSetsDb:
        return DenovoGeneSetsDb(self)

    def get_genotype_data_ids(self, local_only: bool = False) -> list[str]:
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
            self._variants_db.get_genotype_group(genotype_data_id)
        )

    def get_all_genotype_data(self) -> list[GenotypeData]:
        genotype_studies = self._variants_db.get_all_genotype_studies()
        genotype_data_groups = self._variants_db.get_all_genotype_groups()
        return cast(
            list[GenotypeData], genotype_studies + genotype_data_groups
        )

    def get_genotype_data_config(self, genotype_data_id: str) -> Optional[Box]:
        config = self._variants_db.get_genotype_study_config(genotype_data_id)
        if config is not None:
            return config
        return cast(Box, self._variants_db.get_genotype_group_config(
            genotype_data_id
        ))

    def register_genotype_data(self, genotype_data: GenotypeData) -> None:
        self._variants_db.register_genotype_data(genotype_data)

    def unregister_genotype_data(self, genotype_data: GenotypeData) -> None:
        self._variants_db.unregister_genotype_data(genotype_data)

    # Phenotype data
    def get_phenotype_data_ids(self) -> list[str]:
        return self._pheno_registry.get_phenotype_data_ids()

    def get_phenotype_data(
        self, phenotype_data_id: str
    ) -> PhenotypeData:
        return self._pheno_registry.get_phenotype_data(phenotype_data_id)

    def get_all_phenotype_data(self) -> list[PhenotypeData]:
        return self._pheno_registry.get_all_phenotype_data()

    def get_phenotype_data_config(self, phenotype_data_id: str) -> Box:
        return cast(
            Box,
            self._pheno_registry.get_phenotype_data_config(phenotype_data_id)
        )

    # Gene scores
    def has_gene_score(self, gene_score_id: str) -> bool:
        return gene_score_id in self.gene_scores_db

    def get_gene_score(self, gene_score_id: str) -> GeneScore:
        return cast(
            GeneScore, self.gene_scores_db.get_gene_score(gene_score_id)
        )

    def get_gene_score_desc(self, score_id: str) -> GeneScoreDesc:
        return cast(
            GeneScoreDesc, self.gene_scores_db.get_score_desc(score_id)
        )

    def get_all_gene_scores(self) -> list[GeneScore]:
        return cast(list[GeneScore], self.gene_scores_db.get_gene_scores())

    def get_all_gene_score_descs(self) -> list[GeneScoreDesc]:
        return cast(list[GeneScoreDesc], self.gene_scores_db.get_scores())

    # Common reports
    def get_common_report(self, study_id: str) -> Optional[CommonReport]:
        """Load and return common report (dataset statistics) for a study."""
        study = self.get_genotype_data(study_id)
        if study is None or study.is_remote:
            return None
        if not study.config.common_report.enabled:
            return None
        report = CommonReport.load(
            study.config.common_report.file_path)
        if report is None:
            report = CommonReport.build_and_save(study)
        return report

    def get_all_common_report_configs(self) -> list[Box]:
        """Return all common report configuration."""
        configs = []
        local_ids = self.get_genotype_data_ids(True)
        for gd_id in local_ids:
            config = self.get_genotype_data_config(gd_id)
            if config is not None and config.common_report is not None:
                configs.append(config.common_report)
        return configs

    # Gene sets
    def get_gene_sets_collections(self) -> list[dict[str, Any]]:
        return self.gene_sets_db.collections_descriptions

    def has_gene_set_collection(self, gsc_id: str) -> bool:
        return self.gene_sets_db.has_gene_set_collection(gsc_id)

    def get_all_gene_sets(self, collection_id: str) -> list[GeneSet]:
        return self.gene_sets_db.get_all_gene_sets(collection_id)

    def get_gene_set(self, collection_id: str, gene_set_id: str) -> GeneSet:
        return cast(
            GeneSet,
            self.gene_sets_db.get_gene_set(collection_id, gene_set_id)
        )

    def get_denovo_gene_sets(
        self, datasets: list[GenotypeData]
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.denovo_gene_sets_db.get_gene_set_descriptions(datasets)
        )

    def has_denovo_gene_sets(self) -> bool:
        return len(self.denovo_gene_sets_db) > 0

    def get_all_denovo_gene_sets(
        self, types: dict[str, Any],
        datasets: list[Any],
        collection_id: str  # pylint: disable=unused-argument
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.denovo_gene_sets_db.get_all_gene_sets(types, datasets)
        )

    def get_denovo_gene_set(
        self, gene_set_id: str,
        types: dict[str, Any],
        datasets: list[GenotypeData],
        collection_id: str  # pylint: disable=unused-argument
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.denovo_gene_sets_db.get_gene_set(
                gene_set_id, types, datasets
            )
        )

    # Variants DB
    def get_dataset(self, dataset_id: str) -> GenotypeData:
        return cast(GenotypeData, self._variants_db.get(dataset_id))

    # GP
    def get_gp_configuration(self) -> Box:
        return cast(Box, self._gene_profile_db.configuration)

    def get_gp_statistic(self, gene_symbol: str) -> GPStatistic:
        return cast(
            GPStatistic, self._gene_profile_db.get_gp(gene_symbol)
        )

    def query_gp_statistics(
        self,
        page: int,
        symbol_like: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None
    ) -> list[GPStatistic]:
        """Query AGR statistics and return results."""
        rows = self._gene_profile_db.query_gps(
            page, symbol_like, sort_by, order
        )
        statistics = list(map(
            self._gene_profile_db.gp_from_table_row,
            rows
        ))
        return cast(list[GPStatistic], statistics)

    def _construct_import_effect_annotator_config(
        self
    ) -> dict[str, Any]:
        """Construct import effect annotator."""
        genome = self.reference_genome
        gene_models = self.gene_models

        config = {
            "effect_annotator": {
                "genome": genome.resource_id,
                "gene_models": gene_models.resource_id,
                "attributes": [
                    {
                        "source": "allele_effects",
                        "name": "allele_effects",
                        "internal": True
                    },
                    "worst_effect",
                    "gene_effects",
                    "effect_details"
                ]
            }
        }
        return config

    def get_annotation_pipeline_config(self) -> list[dict[str, Any]]:
        """Return the annotation pipeline config."""
        pipeline_config = []
        if self.dae_config.annotation is not None:
            config_filename = self.dae_config.annotation.conf_file
            if not os.path.exists(config_filename):
                raise ValueError(
                    f"annotation config file not found: {config_filename}")

            with open(config_filename, "rt", encoding="utf8") as infile:
                pipeline_config = yaml.safe_load(infile.read())

        pipeline_config.insert(
            0, self._construct_import_effect_annotator_config())
        return pipeline_config

    def get_annotation_pipeline(self) -> AnnotationPipeline:
        """Return the annotation pipeline configured in the GPF instance."""
        if self._annotation_pipeline is None:
            pipeline_config = self.get_annotation_pipeline_config()
            pipeline = build_annotation_pipeline(
                pipeline_config_raw=pipeline_config,
                grr_repository=self.grr)

            self._annotation_pipeline = pipeline

        return self._annotation_pipeline
