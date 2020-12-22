import os
import logging
import pandas as pd
import math
from dae.genome.genomes_db import GenomesDB

from dae.common_reports.common_report_facade import CommonReportFacade

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

from dae.utils.helpers import isnan


logger = logging.getLogger(__name__)


def cached(prop):
    cached_val_name = "_" + prop.__name__

    def wrap(self):
        if getattr(self, cached_val_name, None) is None:
            setattr(self, cached_val_name, prop(self))
        return getattr(self, cached_val_name)

    return wrap


class GPFInstance(object):
    def __init__(
            self,
            dae_config=None,
            config_file="DAE.conf",
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
        self.load_eagerly = load_eagerly

        if load_eagerly:
            self.genomes_db
            self.gene_sets_db
            self._gene_info_config
            self._pheno_db
            self._variants_db
            self._gene_info_config
            self.denovo_gene_sets_db
            self._score_config
            self._scores_factory
            self.genotype_storage_db
            self._common_report_facade
            self._background_facade

    @property  # type: ignore
    @cached
    def genomes_db(self):
        return GenomesDB(
            self.dae_config.dae_data_dir, self.dae_config.genomes_db.conf_file
        )

    @property  # type: ignore
    @cached
    def _pheno_db(self):
        return PhenoDb(dae_config=self.dae_config)

    @property  # type: ignore
    @cached
    def _gene_info_config(self):
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
        return GPFConfigParser.load_config(
            self.dae_config.genomic_scores_db.conf_file, genomic_scores_schema
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
            self.genomes_db,
            self.genotype_storage_db,
        )

    def reload(self):
        reload_properties = [
            "__variants_db",
            "__common_report_facade",
            "_denovo_gene_sets_db",
            "_gene_sets_db",
        ]
        for cached_val_name in reload_properties:
            setattr(self, cached_val_name, None)

    @property  # type: ignore
    @cached
    def _common_report_facade(self):
        return CommonReportFacade(self)

    @property  # type: ignore
    @cached
    def _autism_gene_profile_config(self):
        return GPFConfigParser.load_config(
            self.dae_config.autism_gene_tool_config.conf_file,
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

    def get_genotype_data_ids(self):
        return (
            self._variants_db.get_genotype_studies_ids()
            + self._variants_db.get_genotype_data_groups_ids()
        )

    def get_genotype_data(self, genotype_data_id):
        genotype_data_study = self._variants_db.get_study(genotype_data_id)
        if genotype_data_study:
            return genotype_data_study
        return self._variants_db.get_genotype_data_group(genotype_data_id)

    def get_all_genotype_data(self):
        genotype_studies = self._variants_db.get_all_studies()
        genotype_data_groups = self._variants_db.get_all_genotype_data_groups()
        return genotype_studies + genotype_data_groups

    def get_genotype_data_config(self, genotype_data_id):
        config = self._variants_db.get_study_config(genotype_data_id)
        if config is not None:
            return config
        return self._variants_db.get_genotype_data_group_config(
            genotype_data_id
        )

    def register_genotype_data(self, genotype_data):
        if genotype_data.id in self.get_genotype_data_ids():
            logger.warning(
                f"replacing genotype data instance {genotype_data.id}")

        self._variants_db\
            ._genotype_data_group_cache[genotype_data.id] = genotype_data
        self._variants_db\
            .genotype_data_group_configs[genotype_data.id] = \
            genotype_data.config

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
        return measure_id in study_wrapper.phenotype_data.measures

    def get_measure_description(self, study_wrapper, measure_id):
        measure = study_wrapper.phenotype_data.measures[measure_id]
        out = {
            "instrument_name": measure.instrument_name,
            "measure_name": measure.measure_name,
            "measure_type": measure.measure_type.name,
            "values_domain": measure.values_domain.split(","),
        }
        if not math.isnan(measure.min_value):
            out["min_value"] = measure.min_value
        if not math.isnan(measure.max_value):
            out["max_value"] = measure.max_value
        return out

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

    # Genomes DB
    def get_genome(self):
        return self.genomes_db.get_genome()

    # Common reports
    def get_common_report(self, common_report_id):
        return self._common_report_facade.get_common_report(common_report_id)

    def get_common_report_families_data(self, common_report_id):
        genotype_data = GPFInstance.get_genotype_data(self, common_report_id)
        return self._common_report_facade.get_families_data(genotype_data)

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

    # DAE config
    def get_selected_genotype_data(self):
        return self.dae_config.gpfjs.selected_genotype_data
