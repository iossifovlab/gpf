"""Defines GPFInstance class that gives access to different parts of GPF."""
# pylint: disable=import-outside-toplevel

import os
import logging
import json
from functools import cache, cached_property
from typing import Optional, Union
from pathlib import Path

from dae.utils.fs_utils import find_directory_with_a_file
from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.scores import GenomicScoresDb
from dae.gene.gene_sets_db import GeneSetsDb, \
    build_gene_set_collection_from_resource
from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.common_reports.common_report import CommonReport

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_db import PhenoDb

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.autism_gene_profile import \
    autism_gene_tool_config

from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.annotation.annotation_factory import build_annotation_pipeline


logger = logging.getLogger(__name__)


class GPFInstance:
    """Class to access different parts of a GPF instance."""

    # pylint: disable=too-many-public-methods
    @staticmethod
    def _build_gpf_config(config_filename: Optional[Union[str, Path]] = None):
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
            config_filename: Optional[Union[str, Path]] = None, **kwargs):
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
            dae_config,
            dae_dir,
            **kwargs):

        self.dae_config = dae_config
        self.dae_dir = str(dae_dir)
        assert self.dae_dir is not None

        self._grr = kwargs.get("grr")
        self._reference_genome = kwargs.get("reference_genome")
        self._gene_models = kwargs.get("gene_models")
        self._annotation_pipeline = None

    def load(self):
        """Load all GPF instance attributes."""
        # pylint: disable=pointless-statement
        self.reference_genome
        self.gene_models
        self.gene_sets_db
        self._pheno_db
        self._variants_db
        self.denovo_gene_sets_db
        self.genomic_scores_db
        self.genotype_storages
        self._background_facade
        return self

    @cached_property
    def grr(self):
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
    def reference_genome(self):
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
    def gene_models(self):
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
    def _pheno_db(self):
        return PhenoDb(dae_config=self.dae_config)

    @cached_property
    def gene_scores_db(self):
        """Load and return gene scores db."""
        from dae.gene.gene_scores import GeneScoresDb, GeneScoreCollection
        if self.dae_config.gene_scores_db is None:
            return GeneScoresDb([])

        gene_scores = self.dae_config.gene_scores_db.gene_scores
        collections = []
        for score in gene_scores:
            resource = self.grr.get_resource(score)
            if resource is None:
                logger.error("unable to find gene score: %s", score)
                continue
            collections.append(GeneScoreCollection(resource))

        return GeneScoresDb(collections)

    @cached_property
    def genomic_scores_db(self):
        """Load and return genomic scores db."""
        scores = []
        if self.dae_config.genomic_scores_db is not None:
            for score_def in self.dae_config.genomic_scores_db:
                scores.append((score_def["resource"], score_def["score"]))
            return GenomicScoresDb(self.grr, scores)

        pipeline = self.get_annotation_pipeline()
        if pipeline is not None and len(pipeline.annotators) > 0:
            for annotator in pipeline.annotators:
                schema = annotator.annotation_schema
                resource_id = annotator.config.get("resource_id")
                if resource_id is None:
                    continue

                resource = self.grr.get_resource(resource_id)
                assert resource is not None, resource_id

                config = resource.get_config()

                if "histograms" not in config:
                    continue

                for field_name in schema.public_fields:
                    scores.append((resource_id, field_name))

        return GenomicScoresDb(self.grr, scores)

    @cached_property
    def genotype_storages(self):
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
    def _variants_db(self):
        return VariantsDb(
            self.dae_config,
            self.reference_genome,
            self.gene_models,
            self.genotype_storages,
        )

    @cached_property
    def _autism_gene_profile_db(self):
        config = None if self._autism_gene_profile_config is None else\
            self._autism_gene_profile_config.to_dict()

        agpdb = AutismGeneProfileDB(
            config,
            os.path.join(self.dae_dir, "agpdb")
        )
        return agpdb

    def reload(self):
        """Reload GPF instance studies, de Novo gene sets, etc."""
        self._variants_db.reload()
        self.denovo_gene_sets_db.reload()

    @cached_property
    def _autism_gene_profile_config(self):
        agp_config = self.dae_config.autism_gene_tool_config
        config_filename = None

        if agp_config is None:
            config_filename = os.path.join(
                self.dae_dir, "autismGeneTool.conf")
            if not os.path.exists(config_filename):
                return None
        else:
            if not os.path.exists(agp_config.conf_file):
                return None
            config_filename = agp_config.conf_file

        assert config_filename is not None
        return GPFConfigParser.load_config(
            config_filename,
            autism_gene_tool_config
        )

    @cached_property
    def gene_sets_db(self):
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
    def denovo_gene_sets_db(self):
        return DenovoGeneSetsDb(self)

    @cached_property
    def _background_facade(self):
        return BackgroundFacade(self._variants_db)

    def get_genotype_data_ids(self, local_only=False):
        # pylint: disable=unused-argument
        return (
            self._variants_db.get_all_genotype_study_ids()
            + self._variants_db.get_all_genotype_group_ids()
        )

    def get_genotype_data(self, genotype_data_id):
        genotype_data_study = self._variants_db.get_genotype_study(
            genotype_data_id)
        if genotype_data_study:
            return genotype_data_study
        return self._variants_db.get_genotype_group(genotype_data_id)

    def get_all_genotype_data(self):
        genotype_studies = self._variants_db.get_all_genotype_studies()
        genotype_data_groups = self._variants_db.get_all_genotype_groups()
        return genotype_studies + genotype_data_groups

    def get_genotype_data_config(self, genotype_data_id):
        config = self._variants_db.get_genotype_study_config(genotype_data_id)
        if config is not None:
            return config
        return self._variants_db.get_genotype_group_config(
            genotype_data_id
        )

    def register_genotype_data(self, genotype_data):
        self._variants_db.register_genotype_data(genotype_data)

    def unregister_genotype_data(self, genotype_data):
        self._variants_db.unregister_genotype_data(genotype_data)

    # Phenotype data
    def get_phenotype_db_config(self):
        return self._pheno_db.config

    def get_phenotype_data_ids(self):
        return self._pheno_db.get_phenotype_data_ids()

    def get_phenotype_data(self, phenotype_data_id):
        return self._pheno_db.get_phenotype_data(phenotype_data_id)

    def get_all_phenotype_data(self):
        return self._pheno_db.get_all_phenotype_data()

    def get_phenotype_data_config(self, phenotype_data_id):
        return self._pheno_db.get_phenotype_data_config(phenotype_data_id)

    # Genomic scores
    def get_genomic_scores(self):
        return self.genomic_scores_db.get_scores()

    # Gene scores

    def has_gene_score(self, gene_score_id):
        return gene_score_id in self.gene_scores_db

    def get_gene_score(self, gene_score_id):
        return self.gene_scores_db.get_gene_score(gene_score_id)

    def get_all_gene_scores(self):
        return self.gene_scores_db.get_gene_scores()

    # Common reports
    def get_common_report(self, study_id):
        """Load and return common report (dataset statistics) for a study."""
        study = self.get_genotype_data(study_id)
        if study is None or study.is_remote:
            return None
        try:
            common_report_path = study.config.common_report.file_path
            if not common_report_path or not os.path.exists(
                common_report_path
            ):
                return None

            with open(common_report_path, "r", encoding="utf-8") as crf:
                cr_json = json.load(crf)

            return CommonReport(cr_json)
        except AssertionError:
            return None

    def get_all_common_report_configs(self):
        """Return all common report configuration."""
        configs = []
        local_ids = self.get_genotype_data_ids(True)
        for gd_id in local_ids:
            config = self.get_genotype_data_config(gd_id)
            if config.common_report is not None:
                configs.append(config.common_report)
        return configs

    # Gene sets
    def get_gene_sets_collections(self):
        return self.gene_sets_db.collections_descriptions

    def has_gene_set_collection(self, gsc_id):
        return self.gene_sets_db.has_gene_set_collection(gsc_id)

    def get_all_gene_sets(self, collection_id):
        return self.gene_sets_db.get_all_gene_sets(collection_id)

    def get_gene_set(self, collection_id, gene_set_id):
        return self.gene_sets_db.get_gene_set(collection_id, gene_set_id)

    def get_denovo_gene_sets(self, datasets):
        return self.denovo_gene_sets_db.get_gene_set_descriptions(datasets)

    def has_denovo_gene_sets(self):
        return len(self.denovo_gene_sets_db) > 0

    def get_all_denovo_gene_sets(self, types, datasets):
        return self.denovo_gene_sets_db.get_all_gene_sets(types, datasets)

    def get_denovo_gene_set(self, gene_set_id, types, datasets):
        return self.denovo_gene_sets_db.get_gene_set(
            gene_set_id, types, datasets)

    # Variants DB
    def get_dataset(self, dataset_id):
        return self._variants_db.get(dataset_id)

    # Enrichment
    def get_study_enrichment_config(self, dataset_id):
        return self._background_facade.get_study_enrichment_config(dataset_id)

    def has_background(self, dataset_id, background_name):
        return self._background_facade.has_background(
            dataset_id, background_name)

    def get_study_background(self, dataset_id, background_name):
        return self._background_facade.get_study_background(
            dataset_id, background_name)

    # AGP
    def get_agp_configuration(self):
        return self._autism_gene_profile_db.configuration

    def get_agp_statistic(self, gene_symbol):
        return self._autism_gene_profile_db.get_agp(gene_symbol)

    def query_agp_statistics(
            self, page, symbol_like=None, sort_by=None, order=None):
        """Query AGR statistics and return results."""
        rows = self._autism_gene_profile_db.query_agps(
            page, symbol_like, sort_by, order
        )
        statistics = list(map(
            self._autism_gene_profile_db.agp_from_table_row,
            rows
        ))
        return statistics

    # DAE config
    def get_selected_genotype_data(self):
        if self.dae_config.gpfjs is None:
            return None
        return self.dae_config.gpfjs.selected_genotype_data

    @cache
    def get_annotation_pipeline(self):
        """Return the annotation pipeline configured in the GPF instance."""
        if self._annotation_pipeline is None:
            if self.dae_config.annotation is None:
                self._annotation_pipeline = build_annotation_pipeline(
                    [], grr_repository=self.grr)
                return self._annotation_pipeline
                # TODO: write a test to check that this (or the correct
                # version) works.

            config_filename = self.dae_config.annotation.conf_file
            if not os.path.exists(config_filename):
                logger.error(
                    "missing annotation configuration: %s",
                    config_filename)
                raise ValueError(
                    f"missing annotaiton config file <{config_filename}>")

            self._annotation_pipeline = \
                build_annotation_pipeline(
                    pipeline_config_file=config_filename,
                    grr_repository=self.grr)
        return self._annotation_pipeline
