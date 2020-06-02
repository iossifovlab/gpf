import os
import pandas as pd
from dae.genome.genomes_db import GenomesDB

from dae.common_reports.common_report_facade import CommonReportFacade

from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.weights import GeneWeightsDb
from dae.gene.scores import ScoresFactory
from dae.gene.gene_sets_db import GeneSetsDb
from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_db import PhenoDb

from dae.backends.storage.genotype_storage_factory import (
    GenotypeStorageFactory,
)

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.gene_info import gene_info_conf
from dae.configuration.schemas.genomic_scores import genomic_scores_schema


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
        load_eagerly=False,
    ):
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
            self._pheno_db,
            self.gene_weights_db,
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
    def gene_sets_db(self):
        return GeneSetsDb(self._gene_info_config)

    @property  # type: ignore
    @cached
    def denovo_gene_sets_db(self):
        return DenovoGeneSetsDb(self._variants_db)

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

    # Genomes DB
    def get_genome(self):
        return self.genomes_db.get_genome()

    # Common reports
    def get_common_report(self, common_report_id):
        return self._common_report_facade.get_common_report(common_report_id)

    def get_common_report_families_data(self, common_report_id):
        return self._common_report_facade.get_families_data(common_report_id)

    # Gene sets
    def get_gene_sets_collections(self):
        return self.gene_sets_db.collections_descriptions

    def has_gene_set_collection(self):
        return self.gene_sets_db.has_gene_set_collection()

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
    def get_wdae_wrapper(self, dataset_id):
        return self._variants_db.get_wdae_wrapper(dataset_id)

    def get_selected_genotype_data(self):
        return self.dae_config.gpfjs.selected_genotype_data
