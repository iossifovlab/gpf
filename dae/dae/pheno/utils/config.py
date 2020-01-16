'''
Created on Aug 23, 2016

@author: lubo
'''
import os

from dae.configuration.config_parser_base import ConfigParserBase


class PhenoConfigParser(ConfigParserBase):

    SECTION = 'phenotypeData'

    @staticmethod
    def _assert_pheno_paths(configs):
        for _, config in configs.items():
            if config.dbfile is not None:
                assert os.path.isfile(config.dbfile), config.dbfile
            if config.browser_dbfile is not None:
                assert os.path.isfile(config.browser_dbfile), \
                    config.browser_dbfile
            if config.browser_images_dir is not None:
                assert os.path.isdir(config.browser_images_dir), \
                    config.browser_images_dir

    @classmethod
    def read_directory_configurations(
            cls, configurations_dir, defaults=None, fail_silently=False):
        config_files = [
            (conf_path, os.path.dirname(conf_path))
            for conf_path in cls._collect_config_paths(configurations_dir)
        ]

        configs = [
            cls.read_file_configuration(config_file, work_dir)
            for config_file, work_dir in config_files
        ]
        configs = {
            config.name: config for config in configs if config
        }

        cls._assert_pheno_paths(configs)

        return configs

    @classmethod
    def read_file_configuration(cls, config_file, work_dir, defaults=None):
        config = super(PhenoConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults=None)
        if not config or not config.phenotype_data:
            return None

        config = config.phenotype_data

        cls._assert_pheno_paths({config.name: config})

        return config


class PhenoRegressionConfigParser(ConfigParserBase):
    '''
    A parser for phenotype regression configurations.
    Verifies that the regression configuration is correct.
    '''

    @classmethod
    def parse(cls, config):
        error_message = \
            '{} is not a valid regression config!'.format(config.config_file)

        assert 'regression' in config, error_message

        config = super(PhenoRegressionConfigParser, cls).parse(config)

        for regression, regression_section in config['regression'].items():
            error_message += ' The section "{}" is invalid!'.format(regression)

            assert 'instrument_name' in regression_section, error_message
            assert 'measure_name' in regression_section, error_message
            assert 'display_name' in regression_section, error_message
            assert 'jitter' in regression_section, error_message

            regression_section['jitter'] = float(regression_section['jitter'])

        return config
