'''
Created on Sep 18, 2017

@author: lubo
'''
from dae.configuration.dae_config_parser import DAEConfigParser


class PhenoRegressions(DAEConfigParser):

    @staticmethod
    def _get_regression(regression):
        for reg_id, reg in regression.items():
            reg['id'] = reg_id

        return regression

    @classmethod
    def parse(cls, config):
        config = super(PhenoRegressions, cls).parse_section(config)

        config['regression'] = cls._get_regression(config['regression'])

        return config
