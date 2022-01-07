import os
import logging
import pandas as pd
import math
import json

from box import Box

from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.weights import GeneWeightsDb
from dae.gene.scores import ScoresFactory
from dae.gene.gene_sets_db import GeneSetsDb
from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_db import PhenoDb
from dae.pheno_browser.db import DbManager

from dae.backends.storage.genotype_storage_factory import \
    GenotypeStorageFactory

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.gene_info import gene_info_conf
from dae.configuration.schemas.genomic_scores import genomic_scores_schema
from dae.configuration.schemas.autism_gene_profile import (
    autism_gene_tool_config
)
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.genomic_resources import build_genomic_resource_repository
from dae.annotation.annotation_factory import build_annotation_pipeline

from dae.utils.helpers import isnan
from dae.utils.dae_utils import cached, join_line

logger = logging.getLogger(__name__)


class GPFInstance(object):
    def __init__(
            self,
            dae_config=None,
            config_file="gpf_instance.yaml",
            work_dir=None,
            defaults=None,
            load_eagerly=False):
        if dae_config is None:
            # FIXME Merge defaults with newly-loaded config
            assert not defaults, defaults
            if work_dir is None:
                work_dir = os.environ["DAE_DB_DIR"]
            config_file = os.path.join(work_dir, config_file)
            dae_config = GPFConfigParser.load_config(
                config_file, dae_conf_schema
            )

        self.dae_config = dae_config
        self.dae_db_dir = work_dir
        self.__autism_gene_profile_config = None
        self.load_eagerly = load_eagerly

        if self.dae_config.grr:
            self.grr = build_genomic_resource_repository(self.dae_config.grr)
        else:
            self.grr = build_genomic_resource_repository()

        if load_eagerly:
            self.reference_genome
            self.gene_models
            self.gene_sets_db
            self._gene_info_config
            self._pheno_db
            self._variants_db
            self.denovo_gene_sets_db
            self._score_config
            self._scores_factory
            self.genotype_storage_db
            self._background_facade

    @property  # type: ignore
    @cached
    def reference_genome(self):
        resource = self.grr.get_resource(
            self.dae_config.reference_genome.resource_id)
        assert resource is not None, \
            self.dae_config.reference_genome.resource_id
        result = resource.open()
        return result

    @property  # type: ignore
    @cached
    def gene_models(self):
        resource = self.grr.get_resource(
            self.dae_config.gene_models.resource_id)
        assert resource is not None, \
            self.dae_config.gene_models.resource_id
        result = resource.open()
        return result

    @property  # type: ignore
    @cached
    def _pheno_db(self):
        return PhenoDb(dae_config=self.dae_config)

    @property  # type: ignore
    @cached
    def _gene_info_config(self):
        if self.dae_config.gene_info_db is None or \
                self.dae_config.gene_info_db.conf_file is None:
            logger.warning(
                "gene sets and weights are not configured...")
            return Box({}, default_box=True)

        conf_file = self.dae_config.gene_info_db.conf_file
        logger.debug(
            f"loading gene info config file: {conf_file}")
        if not os.path.exists(conf_file):
            return Box({}, default_box=True)
        return GPFConfigParser.load_config(
            self.dae_config.gene_info_db.conf_file, gene_info_conf
        )

    @property  # type: ignore
    @cached
    def gene_weights_db(self):
        return GeneWeightsDb(self._gene_info_config)

    @property  # type: ignore
    @cached
    def _score_config(self):
        if self.dae_config.genomic_scores_db is None or \
                self.dae_config.genomic_scores_db.conf_file is None:
            logger.warning(
                "scores are not configured...")
            return Box({}, default_box=True)
        conf_file = self.dae_config.genomic_scores_db.conf_file
        if not os.path.exists(conf_file):
            return Box({}, default_box=True)
        return GPFConfigParser.load_config(
            conf_file, genomic_scores_schema
        )

    @property  # type: ignore
    @cached
    def _scores_factory(self):
        return ScoresFactory(self._score_config)

    @property  # type: ignore
    @cached
    def genotype_storage_db(self):
        return GenotypeStorageFactory(self.dae_config)

    @property  # type: ignore
    @cached
    def _variants_db(self):
        return VariantsDb(
            self.dae_config,
            self.reference_genome,
            self.gene_models,
            self.genotype_storage_db,
        )

    @property  # type: ignore
    @cached
    def _autism_gene_profile_db(self):
        config = None if self._autism_gene_profile_config is None else\
            self._autism_gene_profile_config.to_dict()

        agpdb = AutismGeneProfileDB(
            config,
            os.path.join(self.dae_db_dir, "agpdb")
        )
        return agpdb

    def reload(self):
        reload_properties = [
            "__variants_db",
            "_denovo_gene_sets_db",
            "_gene_sets_db",
        ]
        for cached_val_name in reload_properties:
            setattr(self, cached_val_name, None)

    @property  # type: ignore
    @cached
    def _autism_gene_profile_config(self):
        agp_config = self.dae_config.autism_gene_tool_config
        config_filename = None

        if agp_config is None:
            config_filename = os.path.join(
                self.dae_db_dir, "autismGeneTool.conf")
            if not os.path.exists(config_filename):
                return None
        else:
            if not os.path.exists(agp_config.conf_file):
                return None
            else:
                config_filename = agp_config.conf_file

        assert config_filename is not None
        return GPFConfigParser.load_config(
            config_filename,
            autism_gene_tool_config
        )

    @property  # type: ignore
    @cached
    def gene_sets_db(self):
        logger.debug("creating new instance of GeneSetsDb")
        return GeneSetsDb(
            self._gene_info_config, load_eagerly=self.load_eagerly)

    @property  # type: ignore
    @cached
    def denovo_gene_sets_db(self):
        return DenovoGeneSetsDb(self)

    @property  # type: ignore
    @cached
    def _background_facade(self):
        return BackgroundFacade(self._variants_db)

    def get_genotype_data_ids(self, local_only=False):
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

    # Pheno browser

    def get_pheno_config(self, study_wrapper):
        dbname = study_wrapper.config.phenotype_data
        return self._pheno_db.config[dbname]

    def has_pheno_data(self, study_wrapper):
        return study_wrapper.phenotype_data is not None

    def get_instruments(self, study_wrapper):
        return study_wrapper.phenotype_data.instruments.keys()

    def get_pheno_dbfile(self, study_wrapper):
        config = self.get_pheno_config(study_wrapper)
        return config.browser_dbfile

    def get_pheno_images_url(self, study_wrapper):
        config = self.get_pheno_config(study_wrapper)
        return config.browser_images_url

    def get_measures_info(self, study_wrapper):
        dbfile = self.get_pheno_dbfile(study_wrapper)
        images_url = self.get_pheno_images_url(study_wrapper)
        db = DbManager(dbfile=dbfile)
        db.build()
        return {
            "base_image_url": images_url,
            "has_descriptions": db.has_descriptions,
            "regression_names": db.regression_display_names,
        }

    def search_measures(self, study_wrapper, instrument, search_term):
        dbfile = self.get_pheno_dbfile(study_wrapper)
        db = DbManager(dbfile=dbfile)
        db.build()

        measures = db.search_measures(instrument, search_term)

        for m in measures:
            if m["values_domain"] is None:
                m["values_domain"] = ""
            m["measure_type"] = m["measure_type"].name

            m["regressions"] = []
            regressions = db.get_regression_values(m["measure_id"]) or []

            for reg in regressions:
                reg = dict(reg)
                if isnan(reg["pvalue_regression_male"]):
                    reg["pvalue_regression_male"] = "NaN"
                if isnan(reg["pvalue_regression_female"]):
                    reg["pvalue_regression_female"] = "NaN"
                m["regressions"].append(reg)

            yield {
                "measure": m,
            }

    def has_measure(self, study_wrapper, measure_id):
        return study_wrapper.phenotype_data.has_measure(measure_id)

    def get_measure_description(self, study_wrapper, measure_id):
        measure = study_wrapper.phenotype_data.measures[measure_id]

        out = {
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type.name,
            "values_domain": measure.domain,
        }
        if not math.isnan(measure.min_value):
            out["min_value"] = measure.min_value
        if not math.isnan(measure.max_value):
            out["max_value"] = measure.max_value
        return out

    def get_regressions(self, study_wrapper):
        dataset_config = self.get_genotype_data_config(
            study_wrapper.study_id)

        pheno_config = self.get_phenotype_db_config()
        browser_dbfile = \
            pheno_config[dataset_config.phenotype_data].browser_dbfile

        db = DbManager(
            browser_dbfile)
        db.build()

        if db is None:
            return None

        return db.regression_display_names_with_ids

    # Genomic scores

    def get_genomic_scores(self):
        return self._scores_factory.get_scores()

    # Gene weights

    def has_gene_weight(self, weight_id):
        return weight_id in self.gene_weights_db

    def get_gene_weight(self, weight_id):
        return self.gene_weights_db[weight_id]

    def get_all_gene_weights(self):
        return self.gene_weights_db.get_gene_weights()

    # Gene info config
    def get_chromosomes(self):
        csvfile = self._gene_info_config.chromosomes.file
        reader = pd.read_csv(csvfile, delimiter="\t")

        reader["#chrom"] = reader["#chrom"].map(lambda x: x[3:])
        col_rename = {"chromStart": "start", "chromEnd": "end"}
        reader = reader.rename(columns=col_rename)

        cols = ["start", "end", "name", "gieStain"]
        reader["start"] = pd.to_numeric(reader["start"], downcast="integer")
        reader["end"] = pd.to_numeric(reader["end"], downcast="integer")
        reader = (
            reader.groupby("#chrom")[cols]
            .apply(lambda x: x.to_dict(orient="records"))
            .to_dict()
        )

        return [{"name": k, "bands": v} for k, v in reader.items()]

    def get_gene_info_gene_weights(self):
        return self._gene_info_config.gene_weights

    # Common reports
    def get_common_report(self, study_id):
        study = self.get_genotype_data(study_id)
        if study is None or study.is_remote:
            return None
        try:
            common_report_path = study.config.common_report.file_path
            if not common_report_path or not os.path.exists(
                common_report_path
            ):
                return None

            with open(common_report_path, "r") as crf:
                common_report = json.load(crf)

            return common_report
        except AssertionError:
            return None
        return common_report.to_dict()

    def get_all_common_report_configs(self):
        configs = []
        local_ids = self.get_genotype_data_ids(True)
        for gd_id in local_ids:
            config = self.get_genotype_data_config(gd_id)
            if config.common_report is not None:
                configs.append(config.common_report)
        return configs

    def get_common_report_families_data(self, common_report_id):
        genotype_data = GPFInstance.get_genotype_data(self, common_report_id)
        if not genotype_data:
            return None

        data = []
        data.append(
            [
                "familyId",
                "personId",
                "dadId",
                "momId",
                "sex",
                "status",
                "role",
                "genotype_data_study",
            ]
        )

        families = list(genotype_data.families.values())
        families.sort(key=lambda f: f.family_id)
        for f in families:
            for p in f.members_in_order:

                row = [
                    p.family_id,
                    p.person_id,
                    p.dad_id if p.dad_id else "0",
                    p.mom_id if p.mom_id else "0",
                    p.sex,
                    p.status,
                    p.role,
                    genotype_data.name,
                ]

                data.append(row)

        return map(join_line, data)

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

    def query_all_agp_statistics(
            self, symbol_like=None, sort_by=None, order=None):
        rows = self._autism_gene_profile_db.query_agps(
            None, symbol_like, sort_by, order
        )
        statistics = list(map(
            self._autism_gene_profile_db.agp_from_table_row,
            rows
        ))
        return statistics

    def query_agp_statistics(
            self, page, symbol_like=None, sort_by=None, order=None):
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

    def get_annotation_pipeline(self):
        if self._annotation_pipeline is None:

            if self.dae_config.annotation is None:
                self._annotation_pipeline = build_annotation_pipeline(
                    [], grr_repository=self.grr)
                # TODO: write a test to check that this (or the correct
                # version) works.
            config_filename = self.dae_config.annotation.conf_file
            if not os.path.exists(config_filename):
                logger.warning(
                    f"missing annotation configuration: {config_filename}")
                return None
            self._annotation_pipeline = \
                build_annotation_pipeline(
                    pipeline_config_file=config_filename,
                    grr_repository=self.grr)
        return self._annotation_pipeline
