'''
Created on Sep 18, 2017

@author: lubo
'''
from dae.configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class PhenoRegressions(DAEConfigParser):

    @classproperty
    def PARSE_TO_LIST(cls):
        return {
            'regression': {
                'group': 'regression',
                'getter': cls._get_regression,
            }
        }

    CONVERT_LIST_TO_DICT = (
        'regression',
    )

    @staticmethod
    def _get_regression(regression_type, regression_options, pheno_config):
        regression = pheno_config.get(regression_type, dict())
        regression['id'] = regression_type.split('.')[-1]

        yield regression

    @classmethod
    def parse(cls, config):
        config = super(PhenoRegressions, cls).parse_section(config)

        return config
