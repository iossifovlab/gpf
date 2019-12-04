from dae.GenomesDB import GenomesDB

from dae.common_reports.common_report_facade import CommonReportFacade

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.weights import GeneWeightsDb
from dae.gene.score_config_parser import ScoreConfigParser
from dae.gene.scores import ScoresFactory
from dae.gene.gene_sets_db import GeneSetsDb
from dae.gene.denovo_gene_sets_db import DenovoGeneSetsDb

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_factory import PhenoFactory

from dae.backends.storage.genotype_storage_factory import \
    GenotypeStorageFactory


def cached(prop):
    cached_val_name = '_' + prop.__name__

    def wrap(self):
        if getattr(self, cached_val_name, None) is None:
            setattr(self, cached_val_name, prop(self))
        return getattr(self, cached_val_name)

    return wrap


class GPFInstance(object):

    def __init__(
            self, dae_config=None, config_file='DAE.conf', work_dir=None,
            defaults=None, load_eagerly=False):
    
        if dae_config is None:
            dae_config = DAEConfigParser.read_and_parse_file_configuration(
                config_file=config_file, work_dir=work_dir, defaults=defaults
            )
        self.dae_config = dae_config

        if load_eagerly:
            self.genomes_db
            self.pheno_factory
            self.gene_info_config
            self.denovo_gene_sets_db
            self.gene_sets_db
            self.score_config
            self.scores_factory
            self.genotype_storage_factory
            self.variants_db
            self.common_report_facade
            self.background_facade

    @property
    @cached
    def genomes_db(self):
        return GenomesDB(
            self.dae_config.dae_data_dir,
            self.dae_config.genomes_db.conf_file
        )

    @property
    @cached
    def pheno_factory(self):
        return PhenoFactory(dae_config=self.dae_config)

    @property
    @cached
    def gene_info_config(self):
        return GeneInfoConfigParser.read_and_parse_file_configuration(
            self.dae_config.gene_info_db.conf_file,
            self.dae_config.dae_data_dir
        )

    @property
    @cached
    def gene_weights_db(self):
        return GeneWeightsDb(self.gene_info_config.gene_weights)

    @property
    @cached
    def score_config(self):
        return ScoreConfigParser.read_and_parse_file_configuration(
            self.dae_config.genomic_scores_db.conf_file,
            self.dae_config.dae_data_dir
        )

    @property
    @cached
    def scores_factory(self):
        return ScoresFactory(self.score_config)

    @property
    @cached
    def genotype_storage_factory(self):
        return GenotypeStorageFactory(self.dae_config)

    @property
    @cached
    def variants_db(self):
        return VariantsDb(
            self.dae_config, self.pheno_factory, self.gene_weights_db,
            self.genomes_db, self.genotype_storage_factory
        )

    def reload(self):
        self._variants_db = None
        self._denovo_gene_sets_db = None
        self._common_report_facade = None
        self._gene_sets_db = None

    @property
    @cached
    def common_report_facade(self):
        return CommonReportFacade(self.variants_db)

    @property
    @cached
    def gene_sets_db(self):
        return GeneSetsDb(self.variants_db, self.gene_info_config)

    @property
    @cached
    def denovo_gene_sets_db(self):
        return DenovoGeneSetsDb(self.variants_db)

    @property
    @cached
    def background_facade(self):
        return BackgroundFacade(self.variants_db)
