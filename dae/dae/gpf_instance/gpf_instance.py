from dae.GenomesDB import GenomesDB

from dae.common_reports.common_report_facade import CommonReportFacade

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.weights import WeightsFactory
from dae.gene.score_config_parser import ScoreConfigParser
from dae.gene.scores import ScoresFactory
from dae.gene.gene_set_collections import GeneSetsCollections
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_factory import PhenoFactory

from dae.backends.storage.genotype_storage_factory import \
    GenotypeStorageFactory


class GPFInstance(object):

    def __init__(self, config_file='DAE.conf', work_dir=None, defaults=None):
        self.dae_config = DAEConfigParser.read_and_parse_file_configuration(
            config_file=config_file, work_dir=work_dir, defaults=defaults
        )
        self.genomes_db_ = None
        self.pheno_factory_ = None
        self.gene_info_config_ = None
        self.weights_factory_ = None
        self.score_config_ = None
        self.scores_factory_ = None
        self.genotype_storage_factory_ = None
        self.variants_db_ = None
        self.common_report_facade_ = None
        self.gene_sets_collections_ = None
        self.denovo_gene_set_facade_ = None
        self.background_facade_ = None

    @property
    def genomes_db(self):
        if self.genomes_db_ is None:
            self.genomes_db_ = GenomesDB(
                self.dae_config.dae_data_dir,
                self.dae_config.genomes_db.conf_file
            )
        return self.genomes_db_

    @property
    def pheno_factory(self):
        if self.pheno_factory_ is None:
            self.pheno_factory_ = PhenoFactory(dae_config=self.dae_config)
        return self.pheno_factory_

    @property
    def gene_info_config(self):
        if self.gene_info_config_ is None:
            self.gene_info_config_ = \
                GeneInfoConfigParser.read_and_parse_file_configuration(
                    self.dae_config.gene_info_db.conf_file,
                    self.dae_config.dae_data_dir
                )
        return self.gene_info_config_

    @property
    def weights_factory(self):
        if self.weights_factory_ is None:
            self.weights_factory_ = \
                WeightsFactory(config=self.gene_info_config.gene_weights)
        return self.weights_factory_

    @property
    def score_config(self):
        if self.score_config_ is None:
            self.score_config_ = \
                ScoreConfigParser.read_and_parse_file_configuration(
                    self.dae_config.genomic_scores_db.conf_file,
                    self.dae_config.dae_data_dir
                )
        return self.score_config_

    @property
    def scores_factory(self):
        if self.scores_factory_ is None:
            self.scores_factory_ = ScoresFactory(self.score_config)
        return self.scores_factory_

    @property
    def genotype_storage_factory(self):
        if self.genotype_storage_factory_ is None:
            self.genotype_storage_factory_ = GenotypeStorageFactory(
                self.dae_config)
        return self.genotype_storage_factory_

    @property
    def variants_db(self):
        if self.variants_db_ is None:
            self.variants_db_ = VariantsDb(
                self.dae_config, self.pheno_factory, self.weights_factory,
                self.genomes_db, self.genotype_storage_factory
            )
        return self.variants_db_

    @property
    def common_report_facade(self):
        if self.common_report_facade_ is None:
            self.common_report_facade_ = CommonReportFacade(self.variants_db)
        return self.common_report_facade_

    @property
    def gene_sets_collections(self):
        if self.gene_sets_collections_ is None:
            self.gene_sets_collections_ = \
                GeneSetsCollections(self.variants_db, self.gene_info_config)
        return self.gene_sets_collections_

    @property
    def denovo_gene_set_facade(self):
        if self.denovo_gene_set_facade_ is None:
            self.denovo_gene_set_facade_ = DenovoGeneSetFacade(
                self.variants_db
            )
        return self.denovo_gene_set_facade_

    @property
    def background_facade(self):
        if self.background_facade_ is None:
            self.background_facade_ = BackgroundFacade(self.variants_db)
        return self.background_facade_
