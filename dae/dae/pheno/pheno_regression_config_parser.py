'''
Created on Sep 18, 2017

@author: lubo
'''
from dae.configuration.dae_config_parser import ConfigParserBase


class PhenoRegressionConfigParser(ConfigParserBase):

    @staticmethod
    def _get_regression(regression):
        for reg_id, reg in regression.items():
            reg['id'] = reg_id

        return regression

    @classmethod
    def parse(cls, config):
        config = super(PhenoRegressionConfigParser, cls).parse_section(config)

        config['regression'] = cls._get_regression(config['regression'])

        return config
