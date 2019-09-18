from dae.common_reports.common_report_facade import CommonReportFacade

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.studies.variants_db import VariantsDb


class GPFInstance(object):

    def __init__(self, config_file='DAE.conf', work_dir=None, defaults=None):
        self.dae_config = DAEConfigParser.read_and_parse_file_configuration(
            config_file=config_file, work_dir=work_dir, defaults=defaults
        )
        self.variants_db = VariantsDb(self.dae_config)
        self.common_report_facade = CommonReportFacade(self.variants_db)
