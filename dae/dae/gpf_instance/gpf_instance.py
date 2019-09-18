from dae.common_reports.common_report_facade import CommonReportFacade

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.enrichment_tool.background_facade import BackgroundFacade

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.weights import WeightsFactory
from dae.gene.score_config_parser import ScoreConfigParser
from dae.gene.scores import ScoresFactory
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade

from dae.studies.variants_db import VariantsDb

from dae.pheno.pheno_factory import PhenoFactory


class GPFInstance(object):

    def __init__(self, config_file='DAE.conf', work_dir=None, defaults=None):
        self.dae_config = DAEConfigParser.read_and_parse_file_configuration(
            config_file=config_file, work_dir=work_dir, defaults=defaults
        )

        self.pheno_factory = PhenoFactory(dae_config=self.dae_config)

        self.gene_info_config = \
            GeneInfoConfigParser.read_and_parse_file_configuration(
                self.dae_config.gene_info_db.conf_file,
                self.dae_config.dae_data_dir
            )
        self.weights_factory = \
            WeightsFactory(config=self.gene_info_config.gene_weights)

        self.score_config = \
            ScoreConfigParser.read_and_parse_file_configuration(
                self.dae_config.genomic_scores_db.conf_file,
                self.dae_config.dae_data_dir
            )
        self.scores_factory = ScoresFactory(self.score_config)

        self.variants_db = VariantsDb(
            self.dae_config, self.pheno_factory, self.weights_factory
        )

        self.common_report_facade = CommonReportFacade(self.variants_db)

        self.denovo_gene_set_facade = DenovoGeneSetFacade(self.variants_db)

        self.background_facade = BackgroundFacade(self.variants_db)
